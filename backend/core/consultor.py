"""Orquestrador on-demand: consultar(origem, destino) → ResultadoRota.

Fluxo:
  1. Verificar cache TTL
  2. Consultar Google Routes + HERE em paralelo (ThreadPoolExecutor)
  3. Merge de status pelo mais severo
  4. Calcular confiança, links e incidente principal
  5. Salvar no cache e retornar ResultadoRota (dict)
"""
import logging
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from core import google_traffic, here_incidents, status
from core.here_incidents import label_para_exibicao
from core.cache import get_cache

logger = logging.getLogger(__name__)


def _chave_cache(
    origem: str,
    destino: str,
    via: list[str] | None = None,
    rodovia_logica: list[str] | None = None,
) -> str:
    base = f"{origem.strip().lower()}|{destino.strip().lower()}"
    if via:
        base += "|" + "|".join(via)
    codigos = sorted(here_incidents.normalizar_codigos_rodovia(rodovia_logica))
    if codigos:
        base += "|rodovias=" + "|".join(codigos)
    return base


def _is_coord(s: str) -> bool:
    """Verifica se a string é coordenada 'lat,lng'."""
    parts = s.strip().split(",")
    if len(parts) != 2:
        return False
    try:
        float(parts[0].strip())
        float(parts[1].strip())
        return True
    except ValueError:
        return False


def _link_waze(origem: str, destino: str) -> str:
    """Link Waze A→B: live-map/directions com from e to.
    Aceita coordenadas (lat,lng) com prefixo ll., endereços ou place IDs (place.ChIJ...).
    """
    if _is_coord(origem) and _is_coord(destino):
        o = origem.strip().replace(" ", "")
        d = destino.strip().replace(" ", "")
        return f"https://www.waze.com/pt-BR/live-map/directions?from=ll.{o}&to=ll.{d}&navigate=yes"
    o = urllib.parse.quote(origem)
    d = urllib.parse.quote(destino)
    return f"https://www.waze.com/pt-BR/live-map/directions?from={o}&to={d}&navigate=yes"


def _link_gmaps(origem: str, destino: str) -> str:
    """Link Google Maps A→B: /dir/?api=1&origin=&destination=
    Replica o comportamento oficial (Maps URLs API).
    """
    o = urllib.parse.quote(origem.strip())
    d = urllib.parse.quote(destino.strip())
    return f"https://www.google.com/maps/dir/?api=1&origin={o}&destination={d}"


def consultar(
    config: dict,
    origem: str,
    destino: str,
    via: list[str] | None = None,
    rodovia_logica: list[str] | None = None,
) -> dict:
    """Consulta on-demand: retorna ResultadoRota completo.

    Args:
        config: dicionário de configuração (do config.yaml)
        origem:  string de origem (endereço ou "lat,lng")
        destino: string de destino (endereço ou "lat,lng")
        via:     lista de waypoints HERE (e.g. "-23.33,-46.82!passThrough=true")
        rodovia_logica: lista opcional de códigos (e.g. ["BR-116", "BR-101"])

    Returns:
        dict (ResultadoRota) com todos os campos necessários para
        resposta JSON, Excel e dashboard HTML.
    """
    ttl = int((config.get("cache", {}) or {}).get("ttl_segundos", 300))
    cache = get_cache(ttl)
    chave = _chave_cache(origem, destino, via, rodovia_logica)

    # --- Resolver API keys (precisa antes do cache para enriquecer labels) ---
    google_key = google_traffic.resolver_api_key(config)
    here_key = here_incidents.resolver_api_key(config)

    # --- Cache hit ---
    cached = cache.get(chave)
    if cached:
        cached["cache_hit"] = True
        if "origem_label" not in cached and here_key:
            cached["origem_label"] = label_para_exibicao(here_key, cached["origem"])
            cached["destino_label"] = label_para_exibicao(here_key, cached["destino"])
        logger.info(f"Cache hit: {origem} → {destino}")
        return cached

    google_result: dict = {}
    here_result: dict = {}

    # --- Coleta paralela ---
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {}
        if google_key:
            futures["google"] = pool.submit(
                google_traffic.consultar, google_key, origem, destino
            )
        if here_key:
            futures["here"] = pool.submit(
                here_incidents.consultar, here_key, origem, destino, via, rodovia_logica
            )

        for nome, future in futures.items():
            try:
                result = future.result(timeout=45)
                if nome == "google":
                    google_result = result
                else:
                    here_result = result
            except Exception as e:
                logger.error(f"Erro ao coletar {nome}: {e}")

    # --- Merge de status ---
    google_ok = bool(google_result) and not google_result.get("erro") and google_result.get("status") not in ("Erro", "Sem dados", "")
    here_ok = bool(here_result) and not here_result.get("erro") and here_result.get("status_here") not in ("Sem dados", "")
    # Geometria: usa sempre que HERE retornou polyline, independente de haver dados de tráfego
    here_has_route = bool(here_result) and not here_result.get("erro") and bool(here_result.get("route_pts"))

    g_status = google_result.get("status", "Sem dados") if google_ok else "Sem dados"
    h_status = here_result.get("status_here", "Sem dados") if here_ok else "Sem dados"

    status_merged = status.status_final(g_status, h_status)

    # Métricas principais — prefere Google para duração/distância
    atraso_min = int(google_result.get("atraso_min", 0)) if google_ok else 0
    dur_normal = int(google_result.get("duracao_normal_min", 0)) if google_ok else 0
    dur_transito = int(google_result.get("duracao_transito_min", 0)) if google_ok else 0
    distancia_km = float(google_result.get("distancia_km", 0.0)) if google_ok else 0.0
    razao = float(google_result.get("razao_transito", 0.0)) if google_ok else 0.0

    # HERE metrics
    jam_avg = float(here_result.get("jam_factor_avg", 0.0)) if here_ok else 0.0
    jam_max = float(here_result.get("jam_factor_max", 0.0)) if here_ok else 0.0
    vel_atual = float(here_result.get("velocidade_atual_kmh", 0.0)) if here_ok else 0.0
    vel_livre = float(here_result.get("velocidade_livre_kmh", 0.0)) if here_ok else 0.0
    pct_cong = float(here_result.get("pct_congestionado", 0.0)) if here_ok else 0.0
    incidentes = here_result.get("incidentes", []) if here_ok else []
    route_pts = here_result.get("route_pts", []) if here_has_route else []
    route_geojson = here_result.get("route_geojson") if here_has_route else None
    flow_pts = here_result.get("flow_pts", []) if here_ok else []
    flow_fonte = "here" if flow_pts and here_ok else ""
    # Fallback: usa trânsito do Google quando HERE não retorna flow (comportamento Waze)
    if not flow_pts and google_ok:
        flow_pts = google_result.get("traffic_flow_pts", []) or []
        flow_fonte = "google" if flow_pts else ""
    metodo_busca = here_result.get("metodo_busca", "bbox") if here_has_route else "bbox"

    # Incidente principal (mais grave)
    inc_principal = status.incidente_principal(incidentes)

    # Confiança
    confianca_label, confianca_pct = status.calcular_confianca(google_ok, here_ok, atraso_min)

    # Fontes utilizadas
    fontes = []
    if google_ok:
        fontes.append("Google Routes API v2")
    if here_ok:
        fontes.append("HERE Traffic")

    # Links de navegação
    link_waze = _link_waze(origem, destino)
    link_gmaps = _link_gmaps(origem, destino)

    # Labels legíveis para UI (paralelo: origem e destino)
    if here_key:
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_orig = pool.submit(label_para_exibicao, here_key, origem)
            f_dest = pool.submit(label_para_exibicao, here_key, destino)
            origem_label = f_orig.result(timeout=12) or origem
            destino_label = f_dest.result(timeout=12) or destino
    else:
        origem_label, destino_label = origem, destino

    resultado: dict = {
        "origem": origem,
        "destino": destino,
        "origem_label": origem_label,
        "destino_label": destino_label,
        "via": via or [],
        "status": status_merged,
        "status_google": g_status,
        "status_here": h_status,
        "atraso_min": atraso_min,
        "duracao_normal_min": dur_normal,
        "duracao_transito_min": dur_transito,
        "distancia_km": distancia_km,
        "razao_transito": razao,
        "confianca": confianca_label,
        "confianca_pct": confianca_pct,
        "incidente_principal": inc_principal,
        "incidentes": incidentes,
        "jam_factor_avg": jam_avg,
        "jam_factor_max": jam_max,
        "velocidade_atual_kmh": vel_atual,
        "velocidade_livre_kmh": vel_livre,
        "pct_congestionado": pct_cong,
        "fontes": fontes,
        "link_waze": link_waze,
        "link_gmaps": link_gmaps,
        "route_pts": route_pts,
        "route_geojson": route_geojson,
        "flow_pts": flow_pts,
        "flow_fonte": flow_fonte,
        "metodo_busca": metodo_busca,
        "consultado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "cache_hit": False,
        "erros": {
            "google": google_result.get("erro", "") if google_result else "API key não configurada",
            "here": here_result.get("erro", "") if here_result else "API key não configurada",
        },
    }

    cache.set(chave, resultado)
    logger.info(
        f"Consulta: {origem} → {destino} | "
        f"Status={status_merged} | Atraso={atraso_min}min | "
        f"Confiança={confianca_label}({confianca_pct}%)"
    )
    return resultado
