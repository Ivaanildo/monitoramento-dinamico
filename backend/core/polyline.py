"""Utilitários de polyline, corridor e distância geométrica.

Portado de monitor-rodovias/sources/here_traffic.py.
Implementa Ramer-Douglas-Peucker + codificação flexpolyline para corridor HERE.
"""
import logging
import math

logger = logging.getLogger(__name__)

EARTH_R = 6_371_000.0  # raio da Terra em metros


# ===== Geometria de distância =====

def _dist_ponto_segmento_m(p: tuple, a: tuple, b: tuple) -> float:
    """Distância ponto → segmento em metros (projeção equiretangular local)."""
    lat, lon = p
    lat1, lon1 = a
    lat2, lon2 = b

    latr = math.radians(lat)
    x  = math.radians(lon)  * math.cos(latr) * EARTH_R
    y  = math.radians(lat)  * EARTH_R
    x1 = math.radians(lon1) * math.cos(math.radians(lat1)) * EARTH_R
    y1 = math.radians(lat1) * EARTH_R
    x2 = math.radians(lon2) * math.cos(math.radians(lat2)) * EARTH_R
    y2 = math.radians(lat2) * EARTH_R

    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)

    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def dist_ponto_polyline_m(p: tuple, poly_pts: list) -> float:
    """Menor distância (metros) de um ponto a uma polyline."""
    if not poly_pts or len(poly_pts) < 2:
        return float("inf")
    return min(
        _dist_ponto_segmento_m(p, poly_pts[i], poly_pts[i + 1])
        for i in range(len(poly_pts) - 1)
    )


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância haversine em km entre dois pontos."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


# ===== RDP Downsampling (portado de here_traffic.py) =====

def rdp_simplify(pontos: list, epsilon_m: float) -> list:
    """Simplificação Ramer-Douglas-Peucker iterativa.

    Preserva pontos geometricamente significativos (curvas, inflexões)
    em detrimento de pontos em trechos retos.

    Args:
        pontos: lista de tuplas (lat, lng)
        epsilon_m: tolerância em metros

    Returns:
        lista simplificada de tuplas (lat, lng)
    """
    n = len(pontos)
    if n <= 2:
        return list(pontos)

    keep = [False] * n
    keep[0] = True
    keep[n - 1] = True
    stack = [(0, n - 1)]

    while stack:
        start, end = stack.pop()
        if end - start <= 1:
            continue

        max_dist = 0.0
        max_idx = start
        for i in range(start + 1, end):
            d = _dist_ponto_segmento_m(pontos[i], pontos[start], pontos[end])
            if d > max_dist:
                max_dist = d
                max_idx = i

        if max_dist > epsilon_m:
            keep[max_idx] = True
            stack.append((start, max_idx))
            stack.append((max_idx, end))

    return [pontos[i] for i in range(n) if keep[i]]


def downsample_polyline(pts: list, max_pts: int = 300, epsilon_start_m: float = 50.0) -> list:
    """Reduz uma polyline para no máximo max_pts pontos via RDP iterativo.

    Cresce o epsilon em 1.5x a cada passo até atingir o limite desejado.
    Garante compatibilidade com o limite da HERE Routing API (300 pts).
    """
    if len(pts) <= max_pts:
        return list(pts)

    epsilon = epsilon_start_m
    simplified = pts
    while len(simplified) > max_pts and epsilon < 50_000:
        simplified = rdp_simplify(pts, epsilon)
        epsilon *= 1.5

    # Se ainda acima do limite, força keep-every-N
    if len(simplified) > max_pts:
        step = max(1, len(pts) // max_pts)
        simplified = pts[::step]
        if pts[-1] not in simplified:
            simplified = list(simplified) + [pts[-1]]

    return simplified


def encode_corridor(pts: list, radius_m: int = 200) -> str | None:
    """Codifica uma lista de pontos (lat, lng) como corridor string HERE.

    Formato: corridor:{flexpolyline_encoded};r={radius_m}

    Args:
        pts: lista de tuplas (lat, lng) — já simplificadas (≤300 pts)
        radius_m: raio do corridor em metros (padrão: 200m)

    Returns:
        String corridor ou None se flexpolyline não disponível ou pts vazio.
    """
    if not pts:
        return None
    try:
        import flexpolyline as fp
        encoded = fp.encode(pts)
        corridor = f"corridor:{encoded};r={radius_m}"
        # HERE limita a string do corridor a ~1500 chars
        if len(corridor) > 1400:
            # Tenta reduzir ainda mais com RDP mais agressivo
            pts_red = downsample_polyline(pts, max_pts=150)
            encoded = fp.encode(pts_red)
            corridor = f"corridor:{encoded};r={radius_m}"
        return corridor
    except ImportError:
        logger.warning("flexpolyline não instalado — corridor indisponível")
        return None
    except Exception as e:
        logger.warning(f"Erro ao codificar corridor: {e}")
        return None


def decode_polyline(encoded: str) -> list:
    """Decodifica uma flexpolyline string em lista de tuplas (lat, lng).

    Suporta tanto polyline pura quanto formato HERE Routing v8
    (que pode incluir altitude como terceiro elemento — strip para 2D).

    Returns:
        Lista de tuplas (lat, lng) ou [] em caso de erro.
    """
    try:
        import flexpolyline as fp
        decoded = fp.decode(encoded)
        # Garante 2D: (lat, lng) — strip altitude se presente
        return [(p[0], p[1]) for p in decoded]
    except ImportError:
        logger.warning("flexpolyline não instalado — decode_polyline indisponível")
        return []
    except Exception as e:
        logger.warning(f"Erro ao decodificar polyline: {e}")
        return []


def decode_google_polyline(encoded: str) -> list:
    """Decodifica polyline no formato Encoded Polyline Algorithm do Google.

    Returns:
        Lista de tuplas (lat, lng) ou [] em caso de erro.
    """
    if not encoded:
        return []
    try:
        coords = []
        idx, lat, lng = 0, 0, 0
        n = len(encoded)
        while idx < n:
            shift, result = 0, 0
            while True:
                byte = ord(encoded[idx]) - 63
                idx += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break
            dlat = ~(result >> 1) if (result & 1) else (result >> 1)
            shift, result = 0, 0
            while idx < n:
                byte = ord(encoded[idx]) - 63
                idx += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break
            dlng = ~(result >> 1) if (result & 1) else (result >> 1)
            lat += dlat
            lng += dlng
            coords.append((lat / 1e5, lng / 1e5))
        return coords
    except (IndexError, ValueError) as e:
        logger.warning(f"Erro ao decodificar polyline Google: {e}")
        return []


def pts_to_geojson_line(pts: list) -> dict:
    """Converte lista de (lat, lng) em GeoJSON LineString."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[lng, lat] for lat, lng in pts],
        },
        "properties": {},
    }
