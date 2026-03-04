import asyncio
import json

from web import app as web_app


class _FakeCache:
    def get(self, key):
        return None

    def set(self, key, value):
        return None


def test_consultar_rota_continua_funcionando_sem_rodovia_logica(monkeypatch):
    capturado = {}

    def fake_consultar(config, origem, destino, via=None, rodovia_logica=None):
        capturado["rodovia_logica"] = rodovia_logica
        return {"status": "Normal"}

    monkeypatch.setattr(web_app.consultor, "consultar", fake_consultar)

    resposta = asyncio.run(
        web_app.consultar_rota(
            origem="Origem",
            destino="Destino",
            via=["1,2!passThrough=true"],
            rodovia_logica=[],
        )
    )

    payload = json.loads(resposta.body)
    assert payload["status"] == "Normal"
    assert capturado["rodovia_logica"] is None


def test_consultar_rota_aceita_rodovia_logica_opcional(monkeypatch):
    capturado = {}

    def fake_consultar(config, origem, destino, via=None, rodovia_logica=None):
        capturado["rodovia_logica"] = rodovia_logica
        return {"status": "Normal"}

    monkeypatch.setattr(web_app.consultor, "consultar", fake_consultar)

    resposta = asyncio.run(
        web_app.consultar_rota(
            origem="Origem",
            destino="Destino",
            via=[],
            rodovia_logica=["BR-116", "BR-101"],
        )
    )

    payload = json.loads(resposta.body)
    assert payload["status"] == "Normal"
    assert capturado["rodovia_logica"] == ["BR-116", "BR-101"]


def test_listar_favoritos_expoe_rodovia_logica_nas_rotas_predefinidas(monkeypatch, tmp_path):
    favoritos_path = tmp_path / "favoritos.json"
    favoritos_path.write_text(
        json.dumps(
            {
                "favoritos": [],
                "routes": [
                    {
                        "id": "R01",
                        "origem": {"hub": "A"},
                        "destino": {"hub": "B"},
                        "rodovia_logica": ["BR-116", "BR-101"],
                        "here": {"origin": "1,1", "destination": "2,2", "via": []},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(web_app, "_FAVORITOS_PATH", favoritos_path)

    resposta = asyncio.run(web_app.listar_favoritos(user="test"))
    payload = json.loads(resposta.body)

    assert payload["favoritos"][0]["rodovia_logica"] == ["BR-116", "BR-101"]


def test_visao_geral_propaga_rodovia_logica_para_o_consultor(monkeypatch, tmp_path):
    favoritos_path = tmp_path / "favoritos.json"
    favoritos_path.write_text(
        json.dumps(
            {
                "routes": [
                    {
                        "id": "R01",
                        "origem": {"hub": "A"},
                        "destino": {"hub": "B"},
                        "rodovia_logica": ["BR-116"],
                        "here": {"origin": "1,1", "destination": "2,2", "via": []},
                        "waypoints_status": {"distance_km": 10},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    capturado = {}

    def fake_consultar(config, origem, destino, via=None, rodovia_logica=None):
        capturado["rodovia_logica"] = rodovia_logica
        return {"status": "Normal", "incidentes": []}

    monkeypatch.setattr(web_app, "_FAVORITOS_PATH", favoritos_path)
    monkeypatch.setattr(web_app, "get_cache", lambda ttl: _FakeCache())
    monkeypatch.setattr(web_app.consultor, "consultar", fake_consultar)

    resultados = asyncio.run(web_app._obter_resultados_visao_geral())  # noqa: SLF001

    assert len(resultados) == 1
    assert capturado["rodovia_logica"] == ["BR-116"]
