from core import consultor


class _FakeCache:
    def __init__(self):
        self._data = {}

    def get(self, key):
        return self._data.get(key)

    def set(self, key, value):
        self._data[key] = value


def test_chave_cache_considera_rodovia_logica():
    chave_a = consultor._chave_cache("Origem", "Destino", rodovia_logica=["BR-116"])  # noqa: SLF001
    chave_b = consultor._chave_cache("Origem", "Destino", rodovia_logica=["BR-101"])  # noqa: SLF001

    assert chave_a != chave_b


def test_chave_cache_normaliza_rodovia_logica():
    chave_a = consultor._chave_cache("Origem", "Destino", rodovia_logica=["br116"])  # noqa: SLF001
    chave_b = consultor._chave_cache("Origem", "Destino", rodovia_logica=["BR-116"])  # noqa: SLF001

    assert chave_a == chave_b


def test_consultar_repassa_rodovia_logica_e_nao_reutiliza_cache_incorreto(monkeypatch):
    cache = _FakeCache()
    chamadas = []

    monkeypatch.setattr(consultor, "get_cache", lambda ttl: cache)
    monkeypatch.setattr(consultor.google_traffic, "resolver_api_key", lambda config: "")
    monkeypatch.setattr(consultor.here_incidents, "resolver_api_key", lambda config: "here-key")
    monkeypatch.setattr(consultor, "label_para_exibicao", lambda api_key, valor: valor)

    def fake_here(api_key, origem, destino, via=None, rodovia_logica=None):
        chamadas.append(tuple(rodovia_logica or ()))
        return {
            "incidentes": [],
            "jam_factor_avg": 0.0,
            "jam_factor_max": 0.0,
            "pct_congestionado": 0.0,
            "velocidade_atual_kmh": 0.0,
            "velocidade_livre_kmh": 0.0,
            "status_here": "Normal",
            "route_pts": [],
            "route_geojson": None,
            "flow_pts": [],
            "metodo_busca": "bbox",
            "erro": "",
        }

    monkeypatch.setattr(consultor.here_incidents, "consultar", fake_here)

    primeiro = consultor.consultar({}, "Origem", "Destino", rodovia_logica=["BR-116"])
    segundo = consultor.consultar({}, "Origem", "Destino", rodovia_logica=["BR-116"])
    terceiro = consultor.consultar({}, "Origem", "Destino", rodovia_logica=["BR-101"])

    assert chamadas == [("BR-116",), ("BR-101",)]
    assert segundo["cache_hit"] is True
    assert terceiro["cache_hit"] is False
