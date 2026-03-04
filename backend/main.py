"""Projeto Zero — CLI e servidor web on-demand.

Uso:
 
  python main.py --web
  python main.py --web --port 8080
 
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from core.config_loader import load_config
from core.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger("projeto_zero")


# ===== Config =====

def carregar_config(caminho: str = "config.yaml") -> dict:
    p = Path(caminho)
    if p.suffix.lower() not in (".yaml", ".yml"):
        logger.error(f"Config invalido: {caminho} (deve ser .yaml/.yml)")
        sys.exit(1)

    if not p.exists():
        logger.warning(f"Config '{caminho}' nao encontrado. Usando overrides de ambiente.")

    try:
        cfg = load_config(p)
    except ValueError as exc:
        logger.error(str(exc))
        sys.exit(1)

    logger.info(f"Config carregado: {caminho}")
    return cfg


# ===== Modo CLI: --consultar =====

def _print_resultado_cli(resultado: dict) -> None:
    icons = {"Normal": "[OK]", "Moderado": "[!]", "Intenso": "[!!]", "Parado": "[X]"}
    icon = icons.get(resultado.get("status", ""), "[?]")

    print()
    print("=" * 62)
    print(f"  {resultado.get('origem', '')}  ->  {resultado.get('destino', '')}")
    print("=" * 62)
    print(f"  Status    : {icon} {resultado.get('status', 'Sem dados')}")
    print(f"  Atraso    : {resultado.get('atraso_min', 0)} min")
    print(f"  Normal    : {resultado.get('duracao_normal_min', 0)} min")
    print(f"  Trafego   : {resultado.get('duracao_transito_min', 0)} min")
    print(f"  Distancia : {resultado.get('distancia_km', 0)} km")
    print(f"  Confianca : {resultado.get('confianca', '?')} ({resultado.get('confianca_pct', 0)}%)")

    inc = resultado.get("incidente_principal", "")
    if inc:
        print(f"  Incidente : {inc}")

    jam_avg = resultado.get("jam_factor_avg", 0)
    jam_max = resultado.get("jam_factor_max", 0)
    if jam_avg or jam_max:
        print(f"  Jam Avg   : {jam_avg:.1f}  |  Jam Max: {jam_max:.1f}")

    vel = resultado.get("velocidade_atual_kmh", 0)
    if vel:
        print(f"  Vel.Atual : {vel} km/h (livre: {resultado.get('velocidade_livre_kmh', 0)} km/h)")

    fontes = resultado.get("fontes", [])
    print(f"  Fontes    : {', '.join(fontes) if fontes else '(nenhuma - configure as API keys)'}")

    incs = resultado.get("incidentes", [])
    if incs:
        print(f"\n  Incidentes HERE ({len(incs)}):")
        for item in incs:
            closed = " [FECHADA]" if item.get("road_closed") else ""
            print(f"    * {item.get('categoria', '?')} [{item.get('severidade', '?')}]{closed}")
            descricao = item.get("descricao", "")[:120]
            if descricao:
                print(f"      {descricao}")

    erros = {k: v for k, v in (resultado.get("erros") or {}).items() if v}
    if erros:
        print("\n  Avisos das fontes:")
        for k, v in erros.items():
            print(f"    {k}: {v}")

    print()
    print(f"  Waze       : {resultado.get('link_waze', '')}")
    print(f"  Google Maps: {resultado.get('link_gmaps', '')}")
    print(f"  Consultado : {resultado.get('consultado_em', '')} UTC")
    print()


def modo_consultar(config: dict, origem: str, destino: str, as_json: bool = False) -> None:
    from core.consultor import consultar

    logger.info(f"Consultando: '{origem}' -> '{destino}'")
    resultado = consultar(config, origem, destino)

    if as_json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        _print_resultado_cli(resultado)

    if not resultado.get("fontes"):
        logger.warning("Nenhuma fonte disponivel. Configure GOOGLE_MAPS_API_KEY e/ou HERE_API_KEY.")
        sys.exit(2)


# ===== Modo Web: --web =====

def modo_web(config: dict, host: str = "", port: int = 0) -> None:
    from web.app import iniciar

    h = host or (config.get("web", {}) or {}).get("host", "0.0.0.0")
    p = port or int((config.get("web", {}) or {}).get("port", 8000))

    logger.info(f"Iniciando servidor em http://{h}:{p}")
    iniciar(config, host=h, port=p)


# ===== Main =====

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Projeto Zero - Consulta de rotas on-demand",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  python main.py --consultar \"Campinas, SP\" \"Sao Paulo, SP\"\n"
            "  python main.py --consultar \"Campinas, SP\" \"Sao Paulo, SP\" --json\n"
            "  python main.py --web\n"
            "  python main.py --web --port 8080\n"
        ),
    )

    parser.add_argument("--config", default="config.yaml", metavar="ARQUIVO",
                        help="Caminho para config.yaml (padrao: config.yaml)")

    # Modo consulta
    parser.add_argument("--consultar", nargs=2, metavar=("ORIGEM", "DESTINO"),
                        help="Consultar rota no terminal")
    parser.add_argument("--json", action="store_true",
                        help="Saida em JSON (usar com --consultar)")

    # Modo web
    parser.add_argument("--web", action="store_true",
                        help="Iniciar servidor web FastAPI")
    parser.add_argument("--host", default="", metavar="HOST",
                        help="Host do servidor (padrao: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=0, metavar="PORTA",
                        help="Porta do servidor (padrao: 8000)")

    args = parser.parse_args()

    if not args.consultar and not args.web:
        parser.print_help()
        sys.exit(0)

    config = carregar_config(args.config)

    if args.consultar:
        origem, destino = args.consultar
        modo_consultar(config, origem, destino, as_json=args.json)

    if args.web:
        modo_web(config, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
