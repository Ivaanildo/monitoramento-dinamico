"""Consulta HERE Traffic Incidents v7 + Flow v7 para uma rota on-demand.

Estratégia de busca (em ordem de prioridade):
  1. HERE Routing v8  → polyline real da rota → corridor preciso (200m raio)
  2. Fallback: bbox tight (5km padding) quando Routing v8 falha

O corridor reduz o ruído geométrico, mas incidentes ainda passam por filtro
semântico por rodovia quando a rota informa `rodovia_logica`.
"""
import logging
import math
import os
import re
import threading
import urllib.parse
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.polyline import (
    decode_polyline,
    downsample_polyline,
    encode_corridor,
    pts_to_geojson_line,
)

logger = logging.getLogger(__name__)

# ===== HTTP Session thread-local =====
_thread_local = threading.local()


def _get_sessao() -> requests.Session:
    if not hasattr(_thread_local, "sessao"):
        s = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            connect=2,
            read=2,
        )
        s.mount("https://", HTTPAdapter(max_retries=retry))
        _thread_local.sessao = s
    return _thread_local.sessao


def _sanitizar_erro(erro, api_key: str = "") -> str:
    msg = str(erro)
    if api_key:
        msg = msg.replace(api_key, "***")
    return msg


def _validar_json_response(resp, contexto: str = ""):
    content_type = resp.headers.get("Content-Type", "")
    if "json" not in content_type:
        logger.warning(f"{contexto} Content-Type inesperado: {content_type}")
    try:
        return resp.json()
    except ValueError:
        logger.error(f"{contexto} Resposta não é JSON válido")
        return None


# ===== Mapeamento HERE -> categorias =====

CATEGORIA_MAP_STR = {
    "accident": "Colisão",
    "brokenDownVehicle": "Colisão",
    "roadClosure": "Interdição",
    "laneRestriction": "Bloqueio Parcial",
    "roadHazard": "Ocorrência",
    "construction": "Obras na Pista",
    "plannedEvent": "Obras na Pista",
    "congestion": "Engarrafamento",
    "slowTraffic": "Engarrafamento",
    "massEvent": "Engarrafamento",
    "weather": "Condição Climática",
    "vehicleRestriction": "Ocorrência",
    "other": "Ocorrência",
}

CATEGORIA_MAP_INT = {
    0: "Engarrafamento", 1: "Colisão", 2: "Ocorrência", 3: "Obras na Pista",
    4: "Condição Climática", 5: "Ocorrência", 6: "Ocorrência", 7: "Engarrafamento",
    8: "Engarrafamento", 9: "Ocorrência", 10: "Engarrafamento", 11: "Ocorrência",
    12: "Obras na Pista", 13: "Ocorrência", 14: "Colisão",
}

SEVERIDADE_MAP = {1: "Baixa", 2: "Média", 3: "Alta", 4: "Crítica"}
CRITICALITY_TO_ID = {"low": 1, "minor": 2, "major": 3, "critical": 4}

_MAX_VIA_PER_CHUNK = 23  # conservador — limite HERE ~25
_MAX_CORRIDOR_KM = 450.0  # HERE limita corredor a 500km; usamos 450km como margem


def _coords_from_via_str(via_str: str) -> tuple[float, float] | None:
    """Extrai (lat, lng) de string via no formato '-23.33,-46.82!passThrough=true'."""
    try:
        coord_part = via_str.split("!")[0]
        parts = coord_part.split(",")
        if len(parts) == 2:
            return (float(parts[0].strip()), float(parts[1].strip()))
    except (ValueError, IndexError):
        pass
    return None


def _split_pts_por_distancia(pts: list, max_km: float = _MAX_CORRIDOR_KM) -> list:
    """Divide lista de pontos em segmentos onde dist acumulada ≤ max_km.

    O último ponto de cada segmento é repetido como primeiro do próximo
    para garantir continuidade do corredor.
    """
    if not pts:
        return []
    segmentos: list = []
    atual = [pts[0]]
    acum = 0.0
    for i in range(1, len(pts)):
        lat1, lng1 = pts[i - 1]
        lat2, lng2 = pts[i]
        d = _haversine_km(lat1, lng1, lat2, lng2)
        if acum + d > max_km and len(atual) >= 2:
            segmentos.append(atual)
            atual = [pts[i - 1], pts[i]]
            acum = d
        else:
            atual.append(pts[i])
            acum += d
    if len(atual) >= 2:
        segmentos.append(atual)
    elif segmentos:
        segmentos[-1].append(atual[0])
    return segmentos


_HIGHWAY_CODE_PARTS_RE = re.compile(
    r"\b(BR|SP|PR|MG|SC|RS|RJ|GO|MS|MT|BA|TO|PI|CE|PE|AL|SE|RN|PB|PA|AM|MA|RO|AC|AP|RR|DF|ES)\s*[-–]?\s*(\d{2,3})\b",
    re.IGNORECASE,
)

_TIPOS_BLOQUEIO_TOTAL = {"roadClosure"}
_TIPOS_BLOQUEIO_PARCIAL = {"laneRestriction"}
_TIPOS_ACIDENTE = {"accident", "brokenDownVehicle"}
_TIPOS_OBRA = {"construction", "plannedEvent"}
_TIPOS_CLIMA = {"weather"}
_TIPOS_RISCO = {"roadHazard"}

_TOTAL_BLOCK_HINTS = (
    "interdicao total",
    "bloqueio total",
    "via fechada",
    "rodovia fechada",
    "pista fechada",
    "sem passagem",
    "sem transito",
    "transito interrompido",
    "trafego interrompido",
    "totalmente bloqueada",
    "totalmente fechada",
)
_PARTIAL_BLOCK_HINTS = (
    "interdicao parcial",
    "bloqueio parcial",
    "faixa interditada",
    "faixa bloqueada",
    "meia pista",
    "pare e siga",
    "desvio",
    "transito fluindo",
    "trafego fluindo",
)
_ACCIDENT_HINTS = ("acidente", "colisao", "capotamento", "engavetamento")
_WORK_HINTS = ("obra", "obras", "trabalhos", "manutencao")
_CLIMATE_HINTS = ("chuva", "alagamento", "neblina", "clima", "granizo")
_RISK_HINTS = ("risco", "objeto na pista", "queda de carga", "deslizamento", "desmoronamento")


def _texto_normalizado(valor: str) -> str:
    base = unicodedata.normalize("NFKD", str(valor or ""))
    return "".join(ch for ch in base if not unicodedata.combining(ch)).strip().lower()


def _categoria_por_tipo(tipo):
    if isinstance(tipo, str) and tipo:
        return CATEGORIA_MAP_STR.get(tipo, "Ocorrência")
    if isinstance(tipo, int):
        return CATEGORIA_MAP_INT.get(tipo, "Ocorrência")
    return "Ocorrência"


def _detectar_bloqueio_escopo(tipo, road_closed_raw: bool, texto: str) -> str:
    texto_norm = _texto_normalizado(texto)
    if road_closed_raw:
        return "total"
    if isinstance(tipo, str) and tipo in _TIPOS_BLOQUEIO_TOTAL:
        return "total"
    if any(hint in texto_norm for hint in _TOTAL_BLOCK_HINTS):
        return "total"
    if isinstance(tipo, str) and tipo in _TIPOS_BLOQUEIO_PARCIAL:
        return "parcial"
    if any(hint in texto_norm for hint in _PARTIAL_BLOCK_HINTS):
        return "parcial"
    return "nenhum"


def _detectar_causa(tipo, texto: str) -> str:
    texto_norm = _texto_normalizado(texto)
    if isinstance(tipo, str):
        if tipo in _TIPOS_ACIDENTE:
            return "acidente"
        if tipo in _TIPOS_OBRA:
            return "obra"
        if tipo in _TIPOS_CLIMA:
            return "clima"
        if tipo in _TIPOS_RISCO:
            return "risco"
    if any(hint in texto_norm for hint in _ACCIDENT_HINTS):
        return "acidente"
    if any(hint in texto_norm for hint in _WORK_HINTS):
        return "obra"
    if any(hint in texto_norm for hint in _CLIMATE_HINTS):
        return "clima"
    if any(hint in texto_norm for hint in _RISK_HINTS):
        return "risco"

    categoria_tipo = _categoria_por_tipo(tipo)
    if categoria_tipo == "Colisão":
        return "acidente"
    if categoria_tipo == "Obras na Pista":
        return "obra"
    if categoria_tipo == "Condição Climática":
        return "clima"
    return "indefinida"


def _classificar_categoria(tipo, road_closed_raw: bool, texto: str) -> tuple[str, str, str]:
    bloqueio_escopo = _detectar_bloqueio_escopo(tipo, road_closed_raw, texto)
    causa_detectada = _detectar_causa(tipo, texto)
    categoria_fallback = _categoria_por_tipo(tipo)

    if bloqueio_escopo == "total":
        return "Interdição", bloqueio_escopo, causa_detectada
    if bloqueio_escopo == "parcial":
        return "Bloqueio Parcial", bloqueio_escopo, causa_detectada
    if causa_detectada == "acidente":
        return "Colisão", bloqueio_escopo, causa_detectada
    if causa_detectada == "obra":
        return "Obras na Pista", bloqueio_escopo, causa_detectada
    if causa_detectada == "clima":
        return "Condição Climática", bloqueio_escopo, causa_detectada
    if categoria_fallback in {"Engarrafamento", "Obras na Pista", "Condição Climática"}:
        return categoria_fallback, bloqueio_escopo, causa_detectada
    return "Ocorrência", bloqueio_escopo, causa_detectada


def _extrair_codigos_rodovia(*valores) -> list[str]:
    encontrados: list[str] = []
    vistos: set[str] = set()
    for valor in valores:
        if isinstance(valor, (list, tuple, set)):
            itens = valor
        else:
            itens = [valor]
        for item in itens:
            texto = str(item or "")
            for prefixo, numero in _HIGHWAY_CODE_PARTS_RE.findall(texto):
                codigo = f"{prefixo.upper()}-{numero}"
                if codigo not in vistos:
                    vistos.add(codigo)
                    encontrados.append(codigo)
    return encontrados


def normalizar_codigos_rodovia(rodovia_logica: list[str] | None) -> list[str]:
    if not rodovia_logica:
        return []
    return _extrair_codigos_rodovia(rodovia_logica)


# ===== Geocoding =====

_geocode_cache: dict = {}
_geocode_lock = threading.Lock()


def _geocode_endereco(api_key: str, endereco: str):
    """Geocodifica um endereço via HERE Geocoding API. Retorna (lat, lng) ou None."""
    try:
        consulta = endereco if "brasil" in endereco.lower() else f"{endereco}, Brasil"
        resp = _get_sessao().get(
            "https://geocode.search.hereapi.com/v1/geocode",
            params={
                "q": consulta,
                "apiKey": api_key,
                "limit": 1,
                "lang": "pt-BR",
                "in": "countryCode:BRA",
            },
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if items:
            pos = items[0]["position"]
            return (pos["lat"], pos["lng"])
    except Exception as e:
        logger.warning(f"Geocoding falhou para '{endereco}': {_sanitizar_erro(e, api_key)}")
    return None


def _eh_coordenada(valor: str) -> bool:
    """Verifica se a string está no formato 'lat,lng'."""
    try:
        parts = valor.strip().split(",")
        if len(parts) == 2:
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            return -90 <= lat <= 90 and -180 <= lng <= 180
    except (ValueError, IndexError):
        pass
    return False


_revgeocode_cache: dict = {}
_revgeocode_lock = threading.Lock()


def _reverse_geocode(api_key: str, lat: float, lng: float) -> str | None:
    """Converte coordenadas em endereço legível via HERE Reverse Geocoding API."""
    chave = f"{lat:.6f},{lng:.6f}"
    with _revgeocode_lock:
        if chave in _revgeocode_cache:
            return _revgeocode_cache[chave]
    try:
        resp = _get_sessao().get(
            "https://revgeocode.search.hereapi.com/v1/revgeocode",
            params={
                "at": f"{lat},{lng}",
                "apiKey": api_key,
                "limit": 1,
                "lang": "pt-BR",
            },
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if items:
            item = items[0]
            addr = item.get("address", {})
            # label = endereço formatado; title = alternativa; street/city/state = fallback
            label = addr.get("label") or item.get("title") or addr.get("street")
            if label:
                with _revgeocode_lock:
                    _revgeocode_cache[chave] = label
                return label
            # Fallback: montar cidade + estado
            city = addr.get("city") or addr.get("county", "")
            state = addr.get("stateCode", "")
            if city or state:
                label = ", ".join(filter(None, [city, state]))
                with _revgeocode_lock:
                    _revgeocode_cache[chave] = label
                return label
    except Exception as e:
        logger.warning(f"Reverse geocoding falhou para '{chave}': {_sanitizar_erro(e, api_key)}")
    return None


def label_para_exibicao(api_key: str, valor: str) -> str:
    """Retorna label legível para UI: se for coordenada, faz reverse geocode; senão retorna o valor."""
    if not api_key or not valor:
        return valor or ""
    if not _eh_coordenada(valor):
        return valor
    try:
        parts = valor.split(",")
        lat, lng = float(parts[0].strip()), float(parts[1].strip())
        addr = _reverse_geocode(api_key, lat, lng)
        return addr or valor
    except (ValueError, IndexError):
        return valor


def _parse_ou_geocode(api_key: str, endereco: str):
    """Tenta parsear como 'lat,lng'; senão geocodifica (com cache)."""
    try:
        parts = endereco.split(",")
        if len(parts) == 2:
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return (lat, lng)
    except (ValueError, IndexError):
        pass

    with _geocode_lock:
        if endereco in _geocode_cache:
            return _geocode_cache[endereco]

    resultado = _geocode_endereco(api_key, endereco)
    with _geocode_lock:
        _geocode_cache[endereco] = resultado
    return resultado


# ===== HERE Routing v8 → polyline real da rota =====

_routing_cache: dict = {}
_routing_lock = threading.Lock()


def _single_routing_call(api_key: str, origin: str, destination: str,
                          via: list[str] | None = None) -> list:
    """Faz uma única chamada ao HERE Routing v8 e retorna lista de (lat, lng).

    Args:
        origin: "lat,lng"
        destination: "lat,lng"
        via: lista de strings via no formato HERE (e.g. "-23.33,-46.82!passThrough=true")

    Nota: os valores `via` são adicionados à URL sem URL-encoding porque o HERE
    Routing v8 usa `!` e `=` como delimitadores internos do parâmetro (ex:
    `!passThrough=true`). O `requests` codificaria esses chars para `%21` e `%3D`,
    impedindo o parser do HERE de reconhecer a sintaxe especial.
    """
    base_params = {
        "apiKey": api_key,
        "transportMode": "truck",
        "origin": origin,
        "destination": destination,
        "return": "polyline",
        "spans": "truckAttributes",
    }
    # Monta URL base com params normais (URL-encoded)
    url = "https://router.hereapi.com/v8/routes?" + urllib.parse.urlencode(base_params)
    # Adiciona via sem URL-encoding para preservar sintaxe !passThrough=true
    if via:
        for v in via:
            url += "&via=" + v

    try:
        resp = _get_sessao().get(url, timeout=20)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "?"
        body = ""
        try:
            body = e.response.json() if e.response is not None else ""
        except Exception:
            body = (e.response.text or "")[:200] if e.response is not None else ""
        logger.warning(
            f"HERE Routing v8 HTTP {status_code}: {body} | "
            f"via={len(via) if via else 0} waypoints"
        )
        raise
    data = _validar_json_response(resp, "HERE Routing v8")
    if not data:
        return []

    routes = data.get("routes", [])
    if not routes:
        logger.warning("HERE Routing v8: nenhuma rota encontrada")
        return []

    all_pts = []
    for section in routes[0].get("sections", []):
        poly_str = section.get("polyline", "")
        if poly_str:
            pts = decode_polyline(poly_str)
            all_pts.extend(pts)
    return all_pts


def _call_routing_chunks(api_key: str, lat1: float, lng1: float,
                          lat2: float, lng2: float,
                          via: list[str] | None = None) -> list:
    """Chama HERE Routing v8, dividindo em chunks se via > _MAX_VIA_PER_CHUNK.

    Cada chunk usa o último waypoint da fatia anterior como origin do próximo.
    Concatena polylines removendo ponto duplicado na costura.
    """
    origin = f"{lat1},{lng1}"
    destination = f"{lat2},{lng2}"

    if not via or len(via) <= _MAX_VIA_PER_CHUNK:
        return _single_routing_call(api_key, origin, destination, via)

    # Dividir via em fatias de _MAX_VIA_PER_CHUNK
    all_pts = []
    chunk_origin = origin
    for i in range(0, len(via), _MAX_VIA_PER_CHUNK):
        chunk_via = via[i:i + _MAX_VIA_PER_CHUNK]
        is_last = (i + _MAX_VIA_PER_CHUNK) >= len(via)
        if is_last:
            chunk_dest = destination
        else:
            # O último waypoint da fatia se torna o destino deste chunk
            last_via = chunk_via.pop()
            coords = _coords_from_via_str(last_via)
            if not coords:
                logger.warning(f"Não foi possível extrair coords de via: {last_via}")
                return []
            chunk_dest = f"{coords[0]},{coords[1]}"

        pts = _single_routing_call(
            api_key, chunk_origin, chunk_dest,
            chunk_via if chunk_via else None,
        )
        if not pts:
            logger.warning(f"HERE Routing chunk {i // _MAX_VIA_PER_CHUNK + 1} falhou")
            return []

        if all_pts:
            # Remove ponto duplicado na costura
            all_pts.extend(pts[1:])
        else:
            all_pts.extend(pts)

        chunk_origin = chunk_dest
        logger.info(
            f"HERE Routing chunk {i // _MAX_VIA_PER_CHUNK + 1}: "
            f"{len(pts)} pts (via={len(chunk_via)})"
        )

    return all_pts


def _obter_polyline_rota(api_key: str, lat1: float, lng1: float,
                          lat2: float, lng2: float,
                          via: list[str] | None = None) -> list:
    """Chama HERE Routing v8 para obter a polyline real da rota.

    Retorna lista de tuplas (lat, lng) ou [] se falhar.
    Resultado cacheado por (lat1, lng1, lat2, lng2, via) para reutilização.
    """
    via_key = tuple(via) if via else ()
    cache_key = (round(lat1, 4), round(lng1, 4), round(lat2, 4), round(lng2, 4), via_key)
    with _routing_lock:
        if cache_key in _routing_cache:
            return _routing_cache[cache_key]

    try:
        all_pts = _call_routing_chunks(api_key, lat1, lng1, lat2, lng2, via)
        if not all_pts:
            return []

        # RDP downsampling para ≤300 pontos (limite HERE corridor)
        simplified = downsample_polyline(all_pts, max_pts=300)
        logger.info(
            f"HERE Routing v8: {len(all_pts)} pts brutos → "
            f"{len(simplified)} pts simplificados"
            f"{f' (via={len(via)} waypoints)' if via else ''}"
        )

        with _routing_lock:
            _routing_cache[cache_key] = simplified
        return simplified

    except Exception as e:
        logger.warning(f"HERE Routing v8 falhou: {_sanitizar_erro(e, api_key)}")
        return []


# ===== BBox fallback =====

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def _calcular_bbox(lat1: float, lng1: float, lat2: float, lng2: float,
                   padding_km: float = 5.0) -> tuple:
    pad = padding_km * 0.009
    south = max(-90.0, min(lat1, lat2) - pad)
    north = min(90.0, max(lat1, lat2) + pad)
    west = max(-180.0, min(lng1, lng2) - pad)
    east = min(180.0, max(lng1, lng2) + pad)
    return west, south, east, north


def _formatar_bbox(west: float, south: float, east: float, north: float) -> str:
    return f"bbox:{west:.6f},{south:.6f},{east:.6f},{north:.6f}"


def _gerar_bboxes_fallback(lat1: float, lng1: float, lat2: float, lng2: float,
                            dist_km: float = 0.0,
                            padding_km: float = 5.0, max_boxes: int = 6) -> list[str]:
    """Fallback: bboxes tight de 5km de padding distribuídos ao longo da rota.

    Usado somente quando HERE Routing v8 falha. Espaçamento de ~0.09° (~10km)
    entre boxes garante cobertura sem capturar o ruído de toda área urbana.
    """
    west, south, east, north = _calcular_bbox(lat1, lng1, lat2, lng2, padding_km)

    span_lat = abs(lat2 - lat1)
    span_lng = abs(lng2 - lng1)

    # Rota pequena: 1 bbox basta
    if span_lat <= 0.12 and span_lng <= 0.12:
        return [_formatar_bbox(west, south, east, north)]

    half = padding_km * 0.009
    passo = half * 1.8
    span_total = max(span_lat, span_lng)
    n_boxes = min(max_boxes, max(2, int(math.ceil(span_total / passo)) + 1))

    bboxes = set()
    for i in range(n_boxes):
        t = i / (n_boxes - 1) if n_boxes > 1 else 0
        lat = lat1 + (lat2 - lat1) * t
        lng = lng1 + (lng2 - lng1) * t
        bboxes.add(_formatar_bbox(
            max(-180.0, lng - half), max(-90.0, lat - half),
            min(180.0, lng + half), min(90.0, lat + half),
        ))
    return list(bboxes)


# ===== Filtro de relevância para bbox fallback =====

_EM_URBAN_RE = re.compile(
    r'\b(Em|Entre)\s+(Rua|Avenida|Av\.?|Alameda|Travessa|R\s|Largo|Pra[cç]a|Viela|Beco)\b',
    re.IGNORECASE,
)
_NOME_URBANO_RE = re.compile(
    r'^(Rua|Avenida|Av\.?|Alameda|Travessa|R\s|Largo|Pra[cç]a|Viela|Beco)\b',
    re.IGNORECASE,
)


def _tem_referencia_rodovia(incidente: dict) -> bool:
    return bool(_extrair_codigos_rodovia(
        incidente.get("rodovia_afetada", ""),
        incidente.get("descricao", ""),
    ))


def _e_via_urbana(incidente: dict) -> bool:
    rodovia = (incidente.get("rodovia_afetada") or "").strip()
    descricao = (incidente.get("descricao") or "").strip()
    texto_completo = f"{rodovia} {descricao}"
    if _extrair_codigos_rodovia(texto_completo):
        return False
    if rodovia and _NOME_URBANO_RE.match(rodovia):
        return True
    if _EM_URBAN_RE.search(descricao):
        return True
    return False


def _filtrar_relevancia_bbox(incidentes: list, dist_rota_km: float) -> list:
    """Filtra incidentes no modo bbox fallback (sem corridor preciso).

    Rotas curtas (<200km): sem filtro.
    Rotas médias (200-500km): remove vias urbanas óbvias.
    Rotas longas (>500km): mantém apenas com código de rodovia explícito.
    """
    if dist_rota_km < 200:
        return incidentes

    filtrados: list = []
    descartados = {"via_urbana": 0, "sem_codigo": 0}
    for inc in incidentes:
        if dist_rota_km >= 500:
            if _tem_referencia_rodovia(inc):
                filtrados.append(inc)
            else:
                descartados["sem_codigo"] += 1
        else:
            if _e_via_urbana(inc):
                descartados["via_urbana"] += 1
            else:
                filtrados.append(inc)

    total_descartados = sum(descartados.values())
    if total_descartados:
        logger.info(
            f"Filtro bbox ({dist_rota_km:.0f}km): "
            f"{total_descartados} descartados, {len(filtrados)} mantidos "
            f"(via_urbana={descartados['via_urbana']}, sem_codigo={descartados['sem_codigo']})"
        )
    return filtrados


def _incidente_relevante_para_rodovia(
    incidente: dict,
    rodovia_logica: list[str] | None,
) -> tuple[bool, str]:
    codigos_rota = set(normalizar_codigos_rodovia(rodovia_logica))
    if not codigos_rota:
        return True, "sem_regra"

    codigos_incidente = set(_extrair_codigos_rodovia(
        incidente.get("rodovia_afetada", ""),
        incidente.get("descricao", ""),
    ))
    if not codigos_incidente:
        return False, "sem_codigo"
    if codigos_incidente & codigos_rota:
        return True, "compatível"
    return False, "rodovia_divergente"


def _filtrar_relevancia_rodovia(
    incidentes: list,
    rodovia_logica: list[str] | None,
    metodo_busca: str,
) -> list:
    codigos_rota = normalizar_codigos_rodovia(rodovia_logica)
    if not codigos_rota:
        return incidentes

    filtrados: list = []
    descartados = {"sem_codigo": 0, "rodovia_divergente": 0}
    for inc in incidentes:
        relevante, motivo = _incidente_relevante_para_rodovia(inc, codigos_rota)
        if relevante:
            filtrados.append(inc)
        elif motivo in descartados:
            descartados[motivo] += 1

    total_descartados = sum(descartados.values())
    if total_descartados:
        logger.info(
            f"Filtro rodovia ({metodo_busca}): "
            f"{total_descartados} descartados, {len(filtrados)} mantidos "
            f"(sem_codigo={descartados['sem_codigo']}, "
            f"rodovia_divergente={descartados['rodovia_divergente']})"
        )
    return filtrados


# ===== Parsing de incidentes =====

def _extrair_texto(campo) -> str:
    if isinstance(campo, dict):
        return campo.get("value", "")
    return str(campo) if campo else ""


def _severidade(sev_raw, crit_raw: str) -> tuple[int, str]:
    if isinstance(sev_raw, int) and sev_raw in SEVERIDADE_MAP:
        sev_id = sev_raw
    else:
        sev_id = CRITICALITY_TO_ID.get((crit_raw or "").lower(), 2)
    return sev_id, SEVERIDADE_MAP.get(sev_id, "Média")


def _parse_incidente(item: dict) -> dict | None:
    try:
        inc = item.get("incidentDetails", {})
        location = item.get("location", {})

        desc_text = _extrair_texto(inc.get("summary", {}))
        desc_extra = _extrair_texto(inc.get("description", {}))
        type_desc = _extrair_texto(inc.get("typeDescription", {}))

        road_info = inc.get("roadInfo", {}) or {}
        road_name = road_info.get("name", "") or road_info.get("id", "")

        partes = [f"[{road_name}]"] if road_name else []
        vistos: set = set()
        for texto in (desc_text, desc_extra, type_desc):
            if texto and texto not in vistos:
                partes.append(texto)
                vistos.add(texto)
        texto_unificado = " | ".join(partes)

        road_closed_raw = bool(inc.get("roadClosed", False))
        tipo_raw = inc.get("type", "")
        categoria, bloqueio_escopo, causa_detectada = _classificar_categoria(
            tipo_raw,
            road_closed_raw,
            texto_unificado,
        )
        sev_id, severidade = _severidade(inc.get("severity"), inc.get("criticality", ""))

        # Centróide da geometria
        shape = location.get("shape", {}) or {}
        links = shape.get("links", []) or []
        all_pts = []
        for lk in links:
            all_pts.extend(lk.get("points", []) or [])

        lat = lng = None
        if all_pts:
            lat = sum(p.get("lat", 0) for p in all_pts) / len(all_pts)
            lng = sum(p.get("lng", 0) for p in all_pts) / len(all_pts)

        return {
            "categoria": categoria,
            "severidade": severidade,
            "severidade_id": sev_id,
            "descricao": texto_unificado or "Sem descrição",
            "rodovia_afetada": road_name,
            "road_closed": bloqueio_escopo == "total",
            "road_closed_raw": road_closed_raw,
            "bloqueio_escopo": bloqueio_escopo,
            "causa_detectada": causa_detectada,
            "tipo_raw": tipo_raw,
            "latitude": lat,
            "longitude": lng,
            "inicio": inc.get("startTime", ""),
            "fim": inc.get("endTime", ""),
            "fonte": "HERE Traffic",
            "consultado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        logger.warning(f"Erro ao parsear incidente HERE: {e}")
        return None


# ===== Consulta de Incidents via "in" (corridor ou bbox) =====

def _consultar_incidents_zones(api_key: str, zones: list[str]) -> list:
    """Consulta HERE Incidents v7 para uma lista de zones (corridor ou bbox)."""
    resultados_brutos: list = []
    seen_ids: set = set()

    for zone in zones:
        try:
            resp = _get_sessao().get(
                "https://data.traffic.hereapi.com/v7/incidents",
                params={
                    "apiKey": api_key,
                    "in": zone,
                    "locationReferencing": "shape",
                    "lang": "pt-BR",
                },
                timeout=12,
            )
            resp.raise_for_status()
            data = _validar_json_response(resp, contexto="HERE Incidents")
            if data:
                for item in data.get("results", []):
                    item_id = item.get("id", id(item))
                    if item_id not in seen_ids:
                        seen_ids.add(item_id)
                        parsed = _parse_incidente(item)
                        if parsed:
                            resultados_brutos.append(parsed)
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "?"
            try:
                body = e.response.json() if e.response is not None else ""
            except Exception:
                body = (e.response.text or "")[:200] if e.response is not None else ""
            logger.warning(f"HERE Incidents zone falhou HTTP {status_code}: {body}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"HERE Incidents zone falhou: {_sanitizar_erro(e, api_key)}")

    return resultados_brutos


def _consultar_flow_zones(api_key: str, zones: list[str]) -> list:
    """Consulta HERE Flow v7 para uma lista de zones (corridor ou bbox)."""
    flow_results: list = []
    for zone in zones:
        try:
            resp = _get_sessao().get(
                "https://data.traffic.hereapi.com/v7/flow",
                params={
                    "apiKey": api_key,
                    "in": zone,
                    "locationReferencing": "shape",
                },
                timeout=12,
            )
            resp.raise_for_status()
            data = _validar_json_response(resp, contexto="HERE Flow")
            if data:
                flow_results.extend(data.get("results", []))
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "?"
            try:
                body = e.response.json() if e.response is not None else ""
            except Exception:
                body = (e.response.text or "")[:200] if e.response is not None else ""
            logger.warning(f"HERE Flow zone falhou HTTP {status_code}: {body}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"HERE Flow zone falhou: {_sanitizar_erro(e, api_key)}")
    return flow_results


# ===== API principal =====

def consultar(
    api_key: str,
    origem: str,
    destino: str,
    via: list[str] | None = None,
    rodovia_logica: list[str] | None = None,
) -> dict:
    """Consulta incidentes + fluxo HERE para a rota origem→destino.

    Tenta corridor preciso (Routing v8 + flexpolyline) primeiro.
    Fallback automático para bbox tight (5km padding) se Routing v8 falhar.

    Args:
        via: lista de waypoints no formato HERE (e.g. "-23.33,-46.82!passThrough=true")
        rodovia_logica: lista opcional de códigos (e.g. ["BR-116", "BR-101"])

    Returns:
        dict com: incidentes, jam_factor_avg, jam_factor_max, pct_congestionado,
                  velocidade_atual_kmh, velocidade_livre_kmh, status_here,
                  route_pts, route_geojson, metodo_busca, dist_rota_km, erro
    """
    resultado = {
        "incidentes": [],
        "jam_factor_avg": 0.0,
        "jam_factor_max": 0.0,
        "pct_congestionado": 0.0,
        "velocidade_atual_kmh": 0.0,
        "velocidade_livre_kmh": 0.0,
        "status_here": "Sem dados",
        "route_pts": [],
        "route_geojson": None,
        "flow_pts": [],
        "metodo_busca": "nenhum",
        "dist_rota_km": 0.0,
        "fonte": "HERE Traffic",
        "consultado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "erro": "",
    }

    if not api_key:
        resultado["erro"] = "HERE_API_KEY não configurada"
        return resultado

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_orig = pool.submit(_parse_ou_geocode, api_key, origem)
            f_dest = pool.submit(_parse_ou_geocode, api_key, destino)
            origem_coords = f_orig.result(timeout=20)
            destino_coords = f_dest.result(timeout=20)

        if not origem_coords or not destino_coords:
            resultado["erro"] = "Não foi possível geocodificar origem/destino"
            return resultado

        lat1, lng1 = origem_coords
        lat2, lng2 = destino_coords
        dist_rota_km = _haversine_km(lat1, lng1, lat2, lng2)
        resultado["dist_rota_km"] = round(dist_rota_km, 1)

        # -------- Estratégia 1: HERE Routing v8 → corridor --------
        route_pts = _obter_polyline_rota(api_key, lat1, lng1, lat2, lng2, via=via)
        usar_corridor = False
        zones_incidents: list[str] = []
        zones_flow: list[str] = []

        if route_pts:
            # Divide em segmentos ≤ 450km para respeitar limite HERE de 500km/corredor
            segmentos = _split_pts_por_distancia(route_pts)
            corridors_inc = [c for s in segmentos if (c := encode_corridor(s, radius_m=200))]
            corridors_flow = [c for s in segmentos if (c := encode_corridor(s, radius_m=150))]

            if corridors_inc and corridors_flow:
                usar_corridor = True
                zones_incidents = corridors_inc
                zones_flow = corridors_flow
                resultado["route_pts"] = route_pts
                resultado["route_geojson"] = pts_to_geojson_line(route_pts)
                resultado["metodo_busca"] = "corridor"
                logger.info(
                    f"HERE: rota {dist_rota_km:.0f}km | {len(segmentos)} corredor(es) "
                    f"({len(route_pts)} pts) | raio incidents=200m flow=150m"
                )

        # -------- Estratégia 2: bbox tight fallback --------
        if not usar_corridor:
            zones_incidents = _gerar_bboxes_fallback(lat1, lng1, lat2, lng2, dist_rota_km)
            zones_flow = zones_incidents
            resultado["metodo_busca"] = "bbox"
            logger.info(
                f"HERE: rota {dist_rota_km:.0f}km | bbox fallback "
                f"({len(zones_incidents)} bbox(es)) | filtro rodovias={'sim' if dist_rota_km >= 200 else 'nao'}"
            )

        # -------- Incidents + Flow em paralelo --------
        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_inc = pool.submit(_consultar_incidents_zones, api_key, zones_incidents)
            fut_flow = pool.submit(_consultar_flow_zones, api_key, zones_flow)
            incidentes_brutos = fut_inc.result(timeout=30)
            flow_results = fut_flow.result(timeout=30)

        # Se corridor falhou (ambos vazios), tenta bbox fallback
        if usar_corridor and not incidentes_brutos and not flow_results:
            logger.info("HERE corridor sem resultado — tentando bbox fallback")
            zones_bbox = _gerar_bboxes_fallback(lat1, lng1, lat2, lng2, dist_rota_km)
            with ThreadPoolExecutor(max_workers=2) as pool:
                fut_inc = pool.submit(_consultar_incidents_zones, api_key, zones_bbox)
                fut_flow = pool.submit(_consultar_flow_zones, api_key, zones_bbox)
                incidentes_brutos = fut_inc.result(timeout=30)
                flow_results = fut_flow.result(timeout=30)
            usar_corridor = False
            resultado["metodo_busca"] = "bbox_fallback"

        incidentes_pos_bbox = incidentes_brutos
        if not usar_corridor:
            incidentes_pos_bbox = _filtrar_relevancia_bbox(incidentes_brutos, dist_rota_km)
        logger.info(
            f"HERE Incidents: {len(incidentes_brutos)} brutos -> "
            f"{len(incidentes_pos_bbox)} apos bbox"
        )

        incidentes = _filtrar_relevancia_rodovia(
            incidentes_pos_bbox,
            rodovia_logica,
            resultado.get("metodo_busca", "nenhum"),
        )

        resultado["incidentes"] = incidentes
        logger.info(
            f"HERE Incidents: {len(incidentes_brutos)} brutos -> "
            f"{len(incidentes)} relevantes"
        )

        if flow_results:
            total_speed = total_free = total_jam = count = 0
            jam_por_seg: list = []
            road_closed = any(inc.get("road_closed") for inc in incidentes)
            flow_vis: list = []

            for r in flow_results:
                cf = r.get("currentFlow", {})
                speed = cf.get("speed", 0)
                free_flow = cf.get("freeFlow", 0)
                jf = cf.get("jamFactor", 0)

                # Extrai centroide do segmento para coloração no mapa
                location = r.get("location", {})
                seg_pts: list = []
                for lk in (location.get("shape", {}).get("links", []) or []):
                    seg_pts.extend(lk.get("points", []))
                if seg_pts:
                    lat_c = sum(p.get("lat", 0) for p in seg_pts) / len(seg_pts)
                    lng_c = sum(p.get("lng", 0) for p in seg_pts) / len(seg_pts)
                    flow_vis.append({
                        "lat": round(lat_c, 5),
                        "lng": round(lng_c, 5),
                        "jam": round(jf, 1),
                    })

                if speed > 0 and free_flow > 0:
                    total_speed += speed
                    total_free += free_flow
                    total_jam += jf
                    jam_por_seg.append(jf)
                    count += 1

            resultado["flow_pts"] = flow_vis[:400]

            if count > 0:
                # HERE Flow v7 retorna m/s → converter para km/h
                avg_speed = round((total_speed / count) * 3.6, 1)
                avg_free = round((total_free / count) * 3.6, 1)
                avg_jam = round(total_jam / count, 1)
                jam_max = round(max(jam_por_seg), 1)
                segs_cong = sum(1 for j in jam_por_seg if j >= 5)
                pct_cong = round(segs_cong / count * 100, 1)

                if road_closed or jam_max >= 10:
                    status_here = "Parado"
                elif jam_max >= 8 and pct_cong >= 15.0:
                    status_here = "Intenso"
                elif jam_max >= 5 or avg_jam >= 5 or jam_max >= 8:
                    status_here = "Moderado"
                else:
                    status_here = "Normal"

                resultado.update({
                    "jam_factor_avg": avg_jam,
                    "jam_factor_max": jam_max,
                    "pct_congestionado": pct_cong,
                    "velocidade_atual_kmh": avg_speed,
                    "velocidade_livre_kmh": avg_free,
                    "status_here": status_here,
                })
                logger.info(
                    f"HERE Flow: {status_here} | jam_avg={avg_jam} jam_max={jam_max} "
                    f"vel={avg_speed}km/h (livre={avg_free}km/h)"
                )

    except Exception as e:
        resultado["erro"] = f"Erro HERE: {_sanitizar_erro(e, api_key)}"
        logger.error(f"HERE API: {resultado['erro']}")

    return resultado


def resolver_api_key(config: dict) -> str:
    """Resolve a API key HERE: config → env var."""
    key = (config.get("here", {}) or {}).get("api_key", "")
    return key or os.environ.get("HERE_API_KEY", "")
