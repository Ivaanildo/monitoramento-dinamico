#!/usr/bin/env python3
"""
coletor.py - Motor de Polling para o Supabase

Agrupa as rotas definidas em favoritos.json, despacha chamadas ao consultor.py,
e salva o ciclo diretamente no Supabase. Deve ser executado recorrentemente via
GitHub Actions.
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_BRT = timezone(timedelta(hours=-3))

# Adicionar o diretorio pai ('backend') ao PYTHONPATH para conseguir importar 'core'
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from core import consultor, painel_service, rotas_corporativas
from core.config_loader import load_config
from report.excel_simple import gerar_excel_visao_geral
from storage import database
from storage.repository import salvar_snapshot_agregado


async def _consultar_lote_rotas(rotas, config):
    """Gera o consolidado de todas as rotas corporativas e envia para o painel."""
    print(f"Iniciando coleta paralela de {len(rotas)} rotas...")
    loop = asyncio.get_running_loop()

    async def _consultar_uma(rota: dict) -> dict:
        kwargs = rotas_corporativas.converter_para_parametros_consulta(rota)
        try:
            # consultor.consultar e sincrono; executa em thread separada
            resultado_det = await loop.run_in_executor(
                None,
                lambda: consultor.consultar(
                    config,
                    origem=kwargs["origem"],
                    destino=kwargs["destino"],
                    via=kwargs["via"] or None,
                    rodovia_logica=kwargs["rodovia_logica"] or None,
                ),
            )
            return painel_service.converter_para_resumo_painel(rota, resultado_det)
        except Exception as exc:
            print(f"Erro ao consultar rota {rota.get('id')}: {exc}")
            return painel_service.converter_para_resumo_painel(
                rota,
                {"status": "Erro", "erros": {"geral": str(exc)}},
            )

    sem = asyncio.Semaphore(3)

    async def _consultar_uma_seguro(rota: dict) -> dict:
        async with sem:
            return await _consultar_uma(rota)

    linhas_painel = list(await asyncio.gather(*[_consultar_uma_seguro(rota) for rota in rotas]))
    return linhas_painel


async def executar_coleta():
    config = load_config()
    database.init_supabase(config)
    rotas = rotas_corporativas.carregar_rotas(config)

    if not rotas:
        print("Nenhuma rota configurada em favoritos.json!")
        sys.exit(1)

    resultados = await _consultar_lote_rotas(rotas, config)

    print(f"Coleta terminada. {len(resultados)} trechos processados.")
    print("Enviando snapshot agregado para o Supabase...")

    salvar_snapshot_agregado(resultados, "google_routes,here_incidents")

    relatorios_dir = Path(__file__).parent.parent / "relatorios"
    relatorios_dir.mkdir(exist_ok=True)
    nome_arquivo = relatorios_dir / f"painel_{datetime.now(_BRT).strftime('%Y-%m-%d_%H-%M')}.xlsx"
    excel_bytes = gerar_excel_visao_geral(resultados)
    nome_arquivo.write_bytes(excel_bytes)
    print(f"Relatorio Excel salvo: {nome_arquivo}")

    print("Processo finalizado com sucesso!")


if __name__ == "__main__":
    asyncio.run(executar_coleta())
