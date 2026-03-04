import asyncio

from workers import coletor


def test_executar_coleta_inicializa_supabase_antes_de_persistir(monkeypatch):
    eventos = []
    config = {"auth_local": {}, "supabase": {"url": "", "key": ""}}
    rotas = [{"id": "R01"}]
    resultados = [{"trecho": "R01"}]

    monkeypatch.setattr(coletor, "load_config", lambda: config)

    def fake_init_supabase(received_config):
        eventos.append(("init", received_config))
        return None

    async def fake_consultar_lote(received_rotas, received_config):
        eventos.append(("consultar", received_config, received_rotas))
        return resultados

    def fake_salvar_snapshot(received_resultados, fontes):
        eventos.append(("salvar", received_resultados, fontes))

    monkeypatch.setattr(coletor.database, "init_supabase", fake_init_supabase)
    monkeypatch.setattr(coletor.rotas_corporativas, "carregar_rotas", lambda received_config: rotas)
    monkeypatch.setattr(coletor, "_consultar_lote_rotas", fake_consultar_lote)
    monkeypatch.setattr(coletor, "salvar_snapshot_agregado", fake_salvar_snapshot)

    asyncio.run(coletor.executar_coleta())

    assert [evento[0] for evento in eventos] == ["init", "consultar", "salvar"]
    assert eventos[0][1] is config
