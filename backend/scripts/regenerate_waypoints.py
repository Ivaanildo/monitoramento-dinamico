#!/usr/bin/env python3
"""Regenera waypoints para rotas corporativas usando HERE Routing v8.

Substitui o antigo seed_waypoints.py com algoritmo melhorado que garante
progressão geográfica monotônica ao longo da polyline.

Algoritmo:
  1. Chamar HERE Routing v8 SEM waypoints (origin → destination) → polyline limpa
  2. Decodificar polyline com flexpolyline
  3. Amostrar pontos por distância acumulada (intervalo = limite_gap_km)
  4. Garantir progressão: distância acumulada ao longo da polyline só cresce
  5. Validar com audit antes de salvar

Uso:
  python regenerate_waypoints.py --route R10          # rota específica
  python regenerate_waypoints.py --all                # todas as 20 rotas
  python regenerate_waypoints.py --route R10 --dry-run  # preview sem salvar
  python regenerate_waypoints.py --route R10 --verify   # re-chamar HERE com novos WPs
"""
import argparse
import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone

import requests

# Ajusta path para importar core.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.polyline import decode_polyline, haversine

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rotas.json")
HERE_API_KEY = os.environ.get("HERE_API_KEY", "")


def fetch_clean_polyline(origin: str, destination: str) -> list:
    """Chama HERE Routing v8 sem waypoints e retorna polyline limpa."""
    if not HERE_API_KEY:
        raise RuntimeError("HERE_API_KEY não definida no ambiente")

    params = {
        "apiKey": HERE_API_KEY,
        "transportMode": "truck",
        "origin": origin,
        "destination": destination,
        "return": "polyline,summary",
        "routingMode": "fast",
    }
    url = "https://router.hereapi.com/v8/routes?" + urllib.parse.urlencode(params)

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    routes = data.get("routes", [])
    if not routes:
        raise RuntimeError(f"Nenhuma rota encontrada: {origin} → {destination}")

    all_pts = []
    total_length_m = 0
    for section in routes[0].get("sections", []):
        poly_str = section.get("polyline", "")
        if poly_str:
            pts = decode_polyline(poly_str)
            all_pts.extend(pts)
        summary = section.get("summary", {})
        total_length_m += summary.get("length", 0)

    return all_pts, total_length_m / 1000.0  # pts, distance_km


def sample_by_cumulative_distance(pts: list, interval_km: float) -> list:
    """Amostra pontos ao longo da polyline por distância acumulada.

    Garante progressão monotônica: cada ponto selecionado está mais adiante
    na polyline do que o anterior.
    """
    if len(pts) < 2:
        return []

    # Calcula distância acumulada
    cum_dist = [0.0]
    for i in range(1, len(pts)):
        d = haversine(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1])
        cum_dist.append(cum_dist[-1] + d)

    total = cum_dist[-1]
    if total < interval_km:
        return []  # Rota muito curta para waypoints

    # Gera pontos intermediários a cada interval_km
    waypoints = []
    target = interval_km
    while target < total - interval_km * 0.5:  # Não amostrar perto do destino
        # Encontra o segmento que contém target
        for i in range(1, len(pts)):
            if cum_dist[i] >= target:
                # Interpola dentro do segmento
                seg_len = cum_dist[i] - cum_dist[i - 1]
                if seg_len == 0:
                    wp = pts[i]
                else:
                    frac = (target - cum_dist[i - 1]) / seg_len
                    lat = pts[i - 1][0] + frac * (pts[i][0] - pts[i - 1][0])
                    lng = pts[i - 1][1] + frac * (pts[i][1] - pts[i - 1][1])
                    wp = (round(lat, 6), round(lng, 6))
                waypoints.append(wp)
                break
        target += interval_km

    return waypoints


def format_via(lat: float, lng: float) -> str:
    """Formata coordenada como string via HERE."""
    return f"{lat},{lng}!passThrough=true"


def regenerate_route(route: dict, dry_run: bool = False, verify: bool = False):
    """Regenera waypoints para uma rota."""
    rid = route["id"]
    origin = route["here"]["origin"]
    destination = route["here"]["destination"]
    interval_km = route.get("limite_gap_km", 106)

    print(f"\n{'='*60}")
    print(f"Rota {rid}: {route['origem']['hub']} -> {route['destino']['hub']}")
    print(f"Intervalo: {interval_km} km")

    old_via = route["here"].get("via", [])
    print(f"Waypoints atuais: {len(old_via)}")

    # 1. Buscar polyline limpa
    print("Buscando polyline limpa do HERE...")
    pts, distance_km = fetch_clean_polyline(origin, destination)
    print(f"Polyline: {len(pts)} pontos, {distance_km:.1f} km")

    # 2. Amostrar por distância acumulada
    waypoints = sample_by_cumulative_distance(pts, interval_km)
    print(f"Novos waypoints: {len(waypoints)}")

    # 3. Formatar como via strings
    new_via = [format_via(wp[0], wp[1]) for wp in waypoints]

    for i, v in enumerate(new_via):
        print(f"  WP{i+1}: {v.split('!')[0]}")

    if dry_run:
        print("\n[DRY-RUN] Nenhuma alteração salva.")
        return new_via

    # 4. Atualizar rota
    route["here"]["via"] = new_via
    route["waypoints_status"] = {
        "has_waypoints": True,
        "source": "regenerate_waypoints.py: HERE polyline resampling (monotonic)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_points": len(new_via),
        "distance_km": round(distance_km, 1),
    }

    if verify and new_via:
        print("\nVerificando com HERE (com waypoints)...")
        try:
            pts_v, dist_v = fetch_clean_polyline_with_via(origin, destination, new_via)
            print(f"Com waypoints: {dist_v:.1f} km (sem: {distance_km:.1f} km, "
                  f"diff: {dist_v - distance_km:+.1f} km)")
        except Exception as e:
            print(f"Verificacao falhou: {e}")

    return new_via


def fetch_clean_polyline_with_via(origin: str, destination: str, via: list) -> tuple:
    """Chama HERE com waypoints para comparar distância."""
    params = {
        "apiKey": HERE_API_KEY,
        "transportMode": "truck",
        "origin": origin,
        "destination": destination,
        "return": "polyline,summary",
        "routingMode": "fast",
    }
    url = "https://router.hereapi.com/v8/routes?" + urllib.parse.urlencode(params)
    for v in via:
        url += "&via=" + v

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    routes = data.get("routes", [])
    if not routes:
        return [], 0.0

    all_pts = []
    total_m = 0
    for section in routes[0].get("sections", []):
        poly_str = section.get("polyline", "")
        if poly_str:
            all_pts.extend(decode_polyline(poly_str))
        total_m += section.get("summary", {}).get("length", 0)

    return all_pts, total_m / 1000.0


def main():
    parser = argparse.ArgumentParser(description="Regenera waypoints das rotas corporativas")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--route", type=str, help="ID da rota (ex: R10)")
    group.add_argument("--all", action="store_true", help="Todas as 20 rotas")
    parser.add_argument("--dry-run", action="store_true", help="Preview sem salvar")
    parser.add_argument("--verify", action="store_true", help="Re-chamar HERE com novos WPs")
    args = parser.parse_args()

    with open(DATA_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    routes = data["routes"]

    if args.route:
        target = [r for r in routes if r["id"] == args.route.upper()]
        if not target:
            print(f"Rota {args.route} nao encontrada")
            sys.exit(1)
        targets = target
    else:
        targets = routes

    for route in targets:
        regenerate_route(route, dry_run=args.dry_run, verify=args.verify)

    if not args.dry_run:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nSalvo em {DATA_PATH}")


if __name__ == "__main__":
    main()
