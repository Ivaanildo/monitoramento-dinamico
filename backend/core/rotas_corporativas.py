"""Módulo responsável pelas rotas corporativas do painel.

Lê e normaliza o arquivo `rota_logistica.json` legando para uso no `projeto_zero_separado`.
"""
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_cache: dict = {"path": None, "data": [], "ts": 0.0}
_CACHE_TTL = 60


def _clear_cache():
    global _cache
    _cache = {"path": None, "data": [], "ts": 0.0}


def carregar_rotas(config: dict) -> list[dict]:
    """Carrega e normaliza as 20 rotas corporativas.
    
    Busca o caminho do arquivo na chave config['corporativo']['rotas_corporativas'].
    Retorna uma lista de rotas normalizadas.
    """
    caminho = config.get("corporativo", {}).get("rotas_corporativas", "data/rotas.json")
        
    p = Path(caminho)
    # Resolver caminho relativo à raiz do projeto
    if not p.is_absolute():
        p = Path(config.get("__config_path", Path(__file__).parent.parent / "config.yaml")).parent / caminho

    resolved = str(p)
    now = time.monotonic()
    if _cache["path"] == resolved and (now - _cache["ts"]) < _CACHE_TTL:
        return [r.copy() for r in _cache["data"]]

    if not p.exists():
        logger.error(f"Arquivo corporativo não encontrado: {p}")
        return []

    try:
        with open(p, encoding="utf-8-sig") as f:
            dados = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao ler arquivo corporativo {p}: {e}")
        return []

    rotas_legado = dados.get("routes", [])
    rotas_normalizadas = []

    for r in rotas_legado:
        # Normalizar para o formato interno
        rota_id = r.get("id")
        if not rota_id:
            continue
            
        origem = r.get("origem", {})
        destino = r.get("destino", {})
        here_data = r.get("here", {})
        wp_status = r.get("waypoints_status", {})

        hub_origem = origem.get("hub", "")
        hub_destino = destino.get("hub", "")
        
        origem_coords = here_data.get("origin", "")
        destino_coords = here_data.get("destination", "")
        
        # Fallback de lat,lng
        if not origem_coords and origem.get("lat") and origem.get("lng"):
            origem_coords = f"{origem['lat']},{origem['lng']}"
            
        if not destino_coords and destino.get("lat") and destino.get("lng"):
            destino_coords = f"{destino['lat']},{destino['lng']}"

        rota_norm = {
            "id": rota_id,
            "hub_origem": hub_origem,
            "hub_destino": hub_destino,
            "origem": origem_coords,
            "destino": destino_coords,
            "via": here_data.get("via", []),
            "rodovia_logica": r.get("rodovia_logica", []),
            "distance_km": wp_status.get("distance_km", 0),
            "n_waypoints": wp_status.get("n_points", 0),
            "limite_gap_km": r.get("limite_gap_km", 0)
        }
        rotas_normalizadas.append(rota_norm)

    _cache.update({"path": resolved, "data": rotas_normalizadas, "ts": now})
    return rotas_normalizadas


def buscar_rota_por_id(config: dict, rota_id: str) -> dict | None:
    """Busca uma rota corporativa pelo ID (ex: 'R01')."""
    rotas = carregar_rotas(config)
    for r in rotas:
        if r["id"] == rota_id:
            return r
    return None


def converter_para_parametros_consulta(rota: dict) -> dict:
    """Converte uma rota corporativa normalizada em kwargs para `consultor.consultar`."""
    return {
        "origem": rota.get("origem", ""),
        "destino": rota.get("destino", ""),
        "via": rota.get("via", []),
        "rodovia_logica": rota.get("rodovia_logica", [])
    }
