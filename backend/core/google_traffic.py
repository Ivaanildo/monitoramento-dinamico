"""Consulta Google Routes API v2 para tempo de rota com tráfego.

Portado de monitor-rodovias/sources/google_maps.py (versão simplificada
para consulta on-demand de rota única, sem circuit breaker ou pybreaker).
"""
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.polyline import decode_google_polyline, midpoint_by_distance
from core.status import classificar_transito

logger = logging.getLogger(__name__)

# Mapeamento Google speed → jam (para compatibilidade com jamColor no frontend)
_SPEED_TO_JAM = {"NORMAL": 0.5, "SLOW": 5.0, "TRAFFIC_JAM": 9.0}

# ===== HTTP Session thread-local com retry =====
_thread_local = threading.local()
_rate_lock = threading.Lock()
_next_allowed_call_ts = 0.0
_GOOGLE_MAX_INTERMEDIATES_API = 25
_GOOGLE_MAX_INTERMEDIATES_DEFAULT = 10
_GOOGLE_MIN_INTERVAL_MS_DEFAULT = 250


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


def _ler_int_env(nome: str, padrao: int, *, minimo: int, maximo: int | None = None) -> int:
    try:
        valor = int(os.getenv(nome, str(padrao)).strip())
    except (ValueError, AttributeError):
        valor = padrao
    if valor < minimo:
        valor = minimo
    if maximo is not None and valor > maximo:
        valor = maximo
    return valor


def _throttle_google_requests() -> None:
    global _next_allowed_call_ts

    intervalo_ms = _ler_int_env(
        "GOOGLE_ROUTES_MIN_INTERVAL_MS",
        _GOOGLE_MIN_INTERVAL_MS_DEFAULT,
        minimo=0,
    )
    if intervalo_ms <= 0:
        return

    intervalo_s = intervalo_ms / 1000.0
    with _rate_lock:
        agora = time.monotonic()
        espera = _next_allowed_call_ts - agora
        if espera > 0:
            time.sleep(espera)
            agora = time.monotonic()
        _next_allowed_call_ts = agora + intervalo_s


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


def _parse_duration_seconds(value) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        txt = value.strip().lower()
        if txt.endswith("s"):
            txt = txt[:-1]
        try:
            return int(float(txt))
        except ValueError:
            return 0
    return 0


def _traffic_to_flow_pts(polyline_enc: str, intervals: list) -> list:
    """Converte speedReadingIntervals + polyline do Google em flow_pts para mapa.

    Cada intervalo vira um ponto {lat, lng, jam} no centroide do trecho,
    permitindo coloração dinâmica estilo Waze quando HERE não retorna flow.
    """
    if not polyline_enc or not intervals:
        return []
    pts = decode_google_polyline(polyline_enc)
    if not pts:
        return []
    flow = []
    for iv in intervals:
        start = iv.get("startPolylinePointIndex", 0)
        end = iv.get("endPolylinePointIndex", start + 1)
        speed = (iv.get("speed") or "NORMAL").upper()
        jam = _SPEED_TO_JAM.get(speed, 0.5)
        start = max(0, min(start, len(pts) - 1))
        end = max(start + 1, min(end, len(pts)))
        seg = pts[start:end]
        if seg:
            lat_c, lng_c = midpoint_by_distance(seg)
            flow.append({"lat": round(lat_c, 5), "lng": round(lng_c, 5), "jam": jam})
    return flow[:400]


def _parse_coordenadas(valor: str) -> dict:
    """Tenta parsear 'lat,lng'; caso contrário retorna address."""
    try:
        parts = str(valor).split(",")
        if len(parts) == 2:
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return {"location": {"latLng": {"latitude": lat, "longitude": lng}}}
    except (ValueError, IndexError):
        pass
    return {"address": valor}


def _via_here_para_intermediate(via_str: str) -> dict | None:
    """Converte '-23.3,-46.8!passThrough=true' para Waypoint intermediario do Google."""
    if not via_str:
        return None
    try:
        coord = via_str.split("!", 1)[0]
        lat_txt, lng_txt = coord.split(",", 1)
        lat = float(lat_txt.strip())
        lng = float(lng_txt.strip())
    except (ValueError, IndexError, AttributeError):
        return None

    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None

    return {
        "location": {"latLng": {"latitude": lat, "longitude": lng}},
        "via": True,
    }


def _montar_intermediates(via: list[str] | None) -> list[dict]:
    if not via:
        return []

    intermediates: list[dict] = []
    invalidos = 0
    for item in via:
        wp = _via_here_para_intermediate(item)
        if wp:
            intermediates.append(wp)
        else:
            invalidos += 1

    if invalidos:
        logger.warning("Google Routes: %s waypoint(s) 'via' invalido(s) foram ignorados", invalidos)

    limite = _ler_int_env(
        "GOOGLE_ROUTES_MAX_INTERMEDIATES",
        _GOOGLE_MAX_INTERMEDIATES_DEFAULT,
        minimo=0,
        maximo=_GOOGLE_MAX_INTERMEDIATES_API,
    )
    if len(intermediates) > limite:
        logger.info(
            "Google Routes: truncando intermediates de %s para %s (limite configurado)",
            len(intermediates),
            limite,
        )
        return intermediates[:limite]

    return intermediates


def consultar(api_key: str, origem: str, destino: str, via: list[str] | None = None) -> dict:
    """Consulta tempo de rota via Google Routes API v2.

    Returns:
        dict com: status, duracao_normal_min, duracao_transito_min,
                  atraso_min, distancia_km, razao_transito,
                  route_token, traffic_on_polyline, fonte, consultado_em, erro
    """
    resultado = {
        "status": "Erro",
        "duracao_normal_min": 0,
        "duracao_transito_min": 0,
        "atraso_min": 0,
        "distancia_km": 0.0,
        "razao_transito": 0.0,
        "route_token": "",
        "traffic_on_polyline": [],
        "fonte": "Google Routes API v2",
        "consultado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "erro": "",
    }

    if not api_key:
        resultado["erro"] = "GOOGLE_MAPS_API_KEY não configurada"
        return resultado

    try:
        _throttle_google_requests()
        intermediates = _montar_intermediates(via)

        body = {
            "origin": _parse_coordenadas(origem),
            "destination": _parse_coordenadas(destino),
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE_OPTIMAL",
            "computeAlternativeRoutes": False,
            "languageCode": "pt-BR",
            "units": "METRIC",
            "departureTime": (
                datetime.now(timezone.utc) + timedelta(seconds=60)
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "extraComputations": ["TRAFFIC_ON_POLYLINE"],
        }
        if intermediates:
            body["intermediates"] = intermediates

        field_mask = (
            "routes.duration,"
            "routes.staticDuration,"
            "routes.distanceMeters,"
            "routes.warnings,"
            "routes.routeToken,"
            "routes.polyline.encodedPolyline,"
            "routes.travelAdvisory.speedReadingIntervals"
        )

        resp = _get_sessao().post(
            "https://routes.googleapis.com/directions/v2:computeRoutes",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": field_mask,
            },
            json=body,
            timeout=30,
        )

        if resp.status_code >= 400:
            try:
                erro_data = resp.json()
                erro = erro_data.get("error", {}) if isinstance(erro_data, dict) else {}
                msg = erro.get("message", resp.text[:200])
            except (ValueError, AttributeError):
                msg = resp.text[:200]
            resultado["erro"] = f"HTTP_{resp.status_code}: {msg}"
            logger.warning(f"Google Routes API erro: {resultado['erro']}")
            return resultado

        data = _validar_json_response(resp, contexto="Google Routes v2")
        if data is None:
            resultado["erro"] = "Resposta não é JSON válido"
            return resultado

        routes = data.get("routes", [])
        if not routes:
            resultado["erro"] = "Nenhuma rota retornada"
            return resultado

        route = routes[0]
        dur_transito_s = _parse_duration_seconds(route.get("duration"))
        dur_normal_s = _parse_duration_seconds(route.get("staticDuration")) or dur_transito_s

        if dur_normal_s <= 0:
            resultado["erro"] = "Duração normal inválida"
            return resultado

        dur_normal_min = round(dur_normal_s / 60)
        dur_transito_min = max(round(dur_transito_s / 60), dur_normal_min)
        atraso_min = dur_transito_min - dur_normal_min
        razao = round(dur_transito_s / dur_normal_s, 2)
        status = classificar_transito(dur_normal_s, dur_transito_s)
        distancia_km = round(int(route.get("distanceMeters", 0) or 0) / 1000, 1)

        intervals = route.get("travelAdvisory", {}).get("speedReadingIntervals", []) or []
        polyline_enc = (route.get("polyline") or {}).get("encodedPolyline", "")

        # Converte speedReadingIntervals + polyline em flow_pts para mapa estilo Waze
        traffic_flow_pts = _traffic_to_flow_pts(polyline_enc, intervals)

        resultado.update({
            "status": status,
            "duracao_normal_min": dur_normal_min,
            "duracao_transito_min": dur_transito_min,
            "atraso_min": atraso_min,
            "distancia_km": distancia_km,
            "razao_transito": razao,
            "route_token": route.get("routeToken", "") or "",
            "traffic_on_polyline": intervals,
            "traffic_flow_pts": traffic_flow_pts,
            "erro": "",
        })

        logger.info(
            f"Google Routes: {status} | {dur_transito_min}min "
            f"(normal: {dur_normal_min}min, atraso: {atraso_min}min, "
            f"distancia: {distancia_km}km, intermediates: {len(intermediates)})"
        )

    except requests.exceptions.RequestException as e:
        resultado["erro"] = f"Erro de conexão: {_sanitizar_erro(e, api_key)}"
        logger.error(f"Google Routes API: {resultado['erro']}")
    except Exception as e:
        resultado["erro"] = f"Erro inesperado: {_sanitizar_erro(e, api_key)}"
        logger.error(f"Google Routes API: {resultado['erro']}")

    return resultado


def resolver_api_key(config: dict) -> str:
    """Resolve a API key do Google: config → env var."""
    key = (config.get("google", {}) or {}).get("api_key", "")
    return key or os.environ.get("GOOGLE_MAPS_API_KEY", "")
