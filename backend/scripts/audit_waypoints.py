#!/usr/bin/env python3
"""Auditoria de waypoints em rotas.json — detecta backtracking/zigzag.

Algoritmo de detecção (3 métricas por tripla consecutiva A-B-C):
  1. Reversão de bearing: diff > 120° indica backtracking
  2. Progresso monotônico: projeção no vetor O→D deve ser crescente
  3. Razão de desvio: dist(A,B)+dist(B,C) > 2.0×dist(A,C) indica desvio

Reutiliza: core.polyline.haversine()
Custo de API: zero.
"""
import json
import math
import os
import sys

# Ajusta path para importar core.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.polyline import haversine


DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rotas.json")

# ── Thresholds ───────────────────────────────────────────────────────
BEARING_REVERSAL_THRESHOLD = 120   # graus
DETOUR_RATIO_THRESHOLD = 2.0
PROGRESS_TOLERANCE = -0.02         # projeção pode recuar até 2% sem alarme


def initial_bearing(lat1, lon1, lat2, lon2):
    """Bearing inicial (graus, 0-360) de (lat1,lon1) → (lat2,lon2)."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = (math.cos(lat1) * math.sin(lat2)
         - math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    brng = math.degrees(math.atan2(x, y))
    return brng % 360


def bearing_diff(b1, b2):
    """Menor diferença angular entre dois bearings (0-180)."""
    d = abs(b1 - b2) % 360
    return d if d <= 180 else 360 - d


def scalar_projection(point, origin, dest):
    """Projeção escalar de `point` no vetor origin→dest, normalizada [0,1].

    Usa projeção equiretangular (suficiente para distâncias < 3000 km no Brasil).
    """
    cos_mid = math.cos(math.radians((origin[0] + dest[0]) / 2))
    ox, oy = origin[1] * cos_mid, origin[0]
    dx, dy = dest[1] * cos_mid - ox, dest[0] - oy
    px, py = point[1] * cos_mid - ox, point[0] - oy
    denom = dx * dx + dy * dy
    if denom == 0:
        return 0.0
    return (px * dx + py * dy) / denom


def parse_via_coord(via_str):
    """Extrai (lat, lng) de string tipo '-23.33,-46.82!passThrough=true'."""
    coord_part = via_str.split("!")[0]
    lat, lng = coord_part.split(",")
    return float(lat), float(lng)


def audit_route(route):
    """Audita uma rota e retorna dict com anomalias encontradas."""
    rid = route["id"]
    origin = (route["origem"]["lat"], route["origem"]["lng"])
    dest = (route["destino"]["lat"], route["destino"]["lng"])
    via_strs = route.get("here", {}).get("via", [])

    if not via_strs:
        return {"id": rid, "status": "green", "issues": [], "score": 100}

    # Sequência completa: origin + waypoints + dest
    coords = [origin]
    for v in via_strs:
        coords.append(parse_via_coord(v))
    coords.append(dest)

    issues = []

    # ── 1. Reversão de bearing ──
    for i in range(len(coords) - 2):
        a, b, c = coords[i], coords[i + 1], coords[i + 2]
        b_ab = initial_bearing(a[0], a[1], b[0], b[1])
        b_bc = initial_bearing(b[0], b[1], c[0], c[1])
        diff = bearing_diff(b_ab, b_bc)
        if diff > BEARING_REVERSAL_THRESHOLD:
            # Índice do waypoint problemático (i+1 na sequência, mas i na lista via)
            wp_idx = i  # posição em via_strs (0-based), onde i=0 é WP1
            issues.append({
                "type": "bearing_reversal",
                "wp_index": wp_idx,
                "wp_label": f"WP{wp_idx + 1}",
                "bearing_diff": round(diff, 1),
                "coord": b,
                "detail": (f"WP{wp_idx + 1} ({b[0]:.3f},{b[1]:.3f}): "
                           f"bearing reversal {diff:.0f}° "
                           f"(threshold {BEARING_REVERSAL_THRESHOLD}°)")
            })

    # ── 2. Progresso monotônico (projeção no vetor O→D) ──
    projections = []
    for i, pt in enumerate(coords):
        projections.append(scalar_projection(pt, origin, dest))

    for i in range(1, len(projections)):
        if projections[i] < projections[i - 1] + PROGRESS_TOLERANCE:
            regression = projections[i] - projections[i - 1]
            if regression < PROGRESS_TOLERANCE:
                wp_idx = i - 1  # índice em via_strs (0-based)
                if 0 <= wp_idx < len(via_strs):
                    issues.append({
                        "type": "monotonic_regression",
                        "wp_index": wp_idx,
                        "wp_label": f"WP{wp_idx + 1}",
                        "proj_prev": round(projections[i - 1], 4),
                        "proj_curr": round(projections[i], 4),
                        "coord": coords[i],
                        "detail": (f"WP{wp_idx + 1}: projection regresses "
                                   f"{projections[i-1]:.4f} → {projections[i]:.4f}")
                    })

    # ── 3. Razão de desvio ──
    for i in range(len(coords) - 2):
        a, b, c = coords[i], coords[i + 1], coords[i + 2]
        d_ab = haversine(a[0], a[1], b[0], b[1])
        d_bc = haversine(b[0], b[1], c[0], c[1])
        d_ac = haversine(a[0], a[1], c[0], c[1])
        if d_ac > 0:
            ratio = (d_ab + d_bc) / d_ac
        else:
            ratio = float("inf")
        if ratio > DETOUR_RATIO_THRESHOLD:
            wp_idx = i
            if 0 <= wp_idx < len(via_strs):
                issues.append({
                    "type": "detour_ratio",
                    "wp_index": wp_idx,
                    "wp_label": f"WP{wp_idx + 1}",
                    "ratio": round(ratio, 2),
                    "coord": b,
                    "detail": (f"WP{wp_idx + 1}: detour ratio {ratio:.2f}× "
                               f"(threshold {DETOUR_RATIO_THRESHOLD}×)")
                })

    # ── Score e status ──
    # Deduplica issues pelo wp_index
    unique_bad_wps = {iss["wp_index"] for iss in issues}
    n_wps = len(via_strs)
    pct_bad = len(unique_bad_wps) / max(n_wps, 1) * 100

    if not issues:
        status = "green"
        score = 100
    elif pct_bad <= 15:
        status = "yellow"
        score = max(0, 100 - int(pct_bad * 3))
    else:
        status = "red"
        score = max(0, 100 - int(pct_bad * 3))

    return {
        "id": rid,
        "name": f"{route['origem']['hub']} → {route['destino']['hub']}",
        "n_waypoints": n_wps,
        "status": status,
        "score": score,
        "bad_wps": sorted(unique_bad_wps),
        "issues": issues,
    }


def main():
    with open(DATA_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    routes = data["routes"]
    print(f"Auditando {len(routes)} rotas de {DATA_PATH}\n")
    print(f"{'Rota':<6} {'Nome':<45} {'WPs':>4} {'Score':>6} {'Status':<8} {'Problemas'}")
    print("─" * 110)

    all_results = []
    total_issues = 0

    for route in routes:
        result = audit_route(route)
        all_results.append(result)
        n_issues = len(result["issues"])
        total_issues += n_issues

        status_icon = {"green": "✓", "yellow": "⚠", "red": "✗"}.get(result["status"], "?")
        name = result.get("name", "")
        if len(name) > 43:
            name = name[:40] + "..."
        print(f"{result['id']:<6} {name:<45} {result['n_waypoints']:>4} "
              f"{result['score']:>5}% {status_icon} {result['status']:<6} "
              f"{n_issues} issue(s)")

        if result["issues"]:
            for iss in result["issues"]:
                print(f"       └─ {iss['detail']}")

    print("─" * 110)
    greens = sum(1 for r in all_results if r["status"] == "green")
    yellows = sum(1 for r in all_results if r["status"] == "yellow")
    reds = sum(1 for r in all_results if r["status"] == "red")
    print(f"\nResumo: {greens} green, {yellows} yellow, {reds} red — {total_issues} issues total")

    # Retorna resultados para uso programático
    return all_results


if __name__ == "__main__":
    results = main()
    # Exit code não-zero se alguma rota está vermelha
    sys.exit(1 if any(r["status"] == "red" for r in results) else 0)
