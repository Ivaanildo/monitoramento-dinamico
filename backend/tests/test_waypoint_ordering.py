"""Testes de validação de ordenação de waypoints em rotas.json.

Garante que nenhuma rota corporativa tem backtracking/zigzag nos waypoints.
"""
import json
import math
import os

import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rotas.json")

# Thresholds
BEARING_REVERSAL_THRESHOLD = 120   # graus
DETOUR_RATIO_THRESHOLD = 2.5       # teste usa limiar mais generoso
PROGRESS_TOLERANCE = -0.05         # teste permite 5% de regressão


def _load_routes():
    with open(DATA_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    return data["routes"]


def _initial_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = (math.cos(lat1) * math.sin(lat2)
         - math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    return math.degrees(math.atan2(x, y)) % 360


def _bearing_diff(b1, b2):
    d = abs(b1 - b2) % 360
    return d if d <= 180 else 360 - d


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _scalar_projection(point, origin, dest):
    cos_mid = math.cos(math.radians((origin[0] + dest[0]) / 2))
    ox, oy = origin[1] * cos_mid, origin[0]
    dx, dy = dest[1] * cos_mid - ox, dest[0] - oy
    px, py = point[1] * cos_mid - ox, point[0] - oy
    denom = dx * dx + dy * dy
    if denom == 0:
        return 0.0
    return (px * dx + py * dy) / denom


def _parse_via(via_str):
    coord_part = via_str.split("!")[0]
    lat, lng = coord_part.split(",")
    return float(lat), float(lng)


def _get_full_sequence(route):
    """Retorna sequência [origin, wp1, ..., wpN, dest] como lista de (lat, lng)."""
    origin = (route["origem"]["lat"], route["origem"]["lng"])
    dest = (route["destino"]["lat"], route["destino"]["lng"])
    via_strs = route.get("here", {}).get("via", [])
    coords = [origin]
    for v in via_strs:
        coords.append(_parse_via(v))
    coords.append(dest)
    return coords


ROUTES = _load_routes()


@pytest.mark.parametrize("route", ROUTES, ids=[r["id"] for r in ROUTES])
def test_no_backtracking(route):
    """Nenhuma reversão de bearing > 120° entre triplas consecutivas."""
    coords = _get_full_sequence(route)
    if len(coords) < 3:
        return

    violations = []
    for i in range(len(coords) - 2):
        a, b, c = coords[i], coords[i + 1], coords[i + 2]
        b_ab = _initial_bearing(a[0], a[1], b[0], b[1])
        b_bc = _initial_bearing(b[0], b[1], c[0], c[1])
        diff = _bearing_diff(b_ab, b_bc)
        if diff > BEARING_REVERSAL_THRESHOLD:
            wp_label = f"WP{i + 1}" if i < len(coords) - 2 else "dest"
            violations.append(f"{wp_label} bearing reversal {diff:.0f}°")

    assert not violations, (
        f"Route {route['id']} has bearing reversals: {'; '.join(violations)}"
    )


@pytest.mark.parametrize("route", ROUTES, ids=[r["id"] for r in ROUTES])
def test_monotonic_progress(route):
    """Projeção no vetor O→D deve ser crescente (com tolerância de 5%)."""
    coords = _get_full_sequence(route)
    if len(coords) < 3:
        return

    origin, dest = coords[0], coords[-1]
    projections = [_scalar_projection(pt, origin, dest) for pt in coords]

    violations = []
    for i in range(1, len(projections)):
        regression = projections[i] - projections[i - 1]
        if regression < PROGRESS_TOLERANCE:
            wp_label = f"WP{i}" if i < len(coords) - 1 else "dest"
            violations.append(
                f"{wp_label} regresses {projections[i-1]:.4f} -> {projections[i]:.4f}"
            )

    assert not violations, (
        f"Route {route['id']} has monotonic regressions: {'; '.join(violations)}"
    )


@pytest.mark.parametrize("route", ROUTES, ids=[r["id"] for r in ROUTES])
def test_detour_ratio(route):
    """Nenhuma tripla com razão de desvio > 2.5."""
    coords = _get_full_sequence(route)
    if len(coords) < 3:
        return

    violations = []
    for i in range(len(coords) - 2):
        a, b, c = coords[i], coords[i + 1], coords[i + 2]
        d_ab = _haversine(a[0], a[1], b[0], b[1])
        d_bc = _haversine(b[0], b[1], c[0], c[1])
        d_ac = _haversine(a[0], a[1], c[0], c[1])
        if d_ac > 0:
            ratio = (d_ab + d_bc) / d_ac
        else:
            ratio = float("inf")
        if ratio > DETOUR_RATIO_THRESHOLD:
            wp_label = f"WP{i + 1}"
            violations.append(f"{wp_label} detour ratio {ratio:.2f}x")

    assert not violations, (
        f"Route {route['id']} has detour violations: {'; '.join(violations)}"
    )


@pytest.mark.parametrize("route", ROUTES, ids=[r["id"] for r in ROUTES])
def test_waypoints_count_matches(route):
    """n_points no waypoints_status deve bater com len(via)."""
    via = route.get("here", {}).get("via", [])
    status = route.get("waypoints_status", {})
    n_points = status.get("n_points", 0)
    assert n_points == len(via), (
        f"Route {route['id']}: n_points={n_points} but len(via)={len(via)}"
    )
