from core import google_traffic


def test_via_here_para_intermediate_valido():
    wp = google_traffic._via_here_para_intermediate("-23.333027,-46.823893!passThrough=true")  # noqa: SLF001
    assert wp == {
        "location": {"latLng": {"latitude": -23.333027, "longitude": -46.823893}},
        "via": True,
    }


def test_via_here_para_intermediate_invalido():
    assert google_traffic._via_here_para_intermediate("sem-coordenadas") is None  # noqa: SLF001


def test_montar_intermediates_aplica_limite_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_ROUTES_MAX_INTERMEDIATES", "2")
    via = [
        "-1.0,-1.0!passThrough=true",
        "-2.0,-2.0!passThrough=true",
        "-3.0,-3.0!passThrough=true",
    ]

    intermediates = google_traffic._montar_intermediates(via)  # noqa: SLF001
    assert len(intermediates) == 2
    assert intermediates[0]["via"] is True


def test_montar_intermediates_ignora_invalidos(monkeypatch):
    monkeypatch.setenv("GOOGLE_ROUTES_MAX_INTERMEDIATES", "25")
    via = [
        "-1.0,-1.0!passThrough=true",
        "invalido",
        "-2.0,-2.0!passThrough=true",
    ]

    intermediates = google_traffic._montar_intermediates(via)  # noqa: SLF001
    assert len(intermediates) == 2
