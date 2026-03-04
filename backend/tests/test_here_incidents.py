from core import here_incidents


def _item(
    tipo="accident",
    road_closed=False,
    summary="",
    description="",
    type_description="",
    road_name="BR-116",
):
    return {
        "incidentDetails": {
            "type": tipo,
            "roadClosed": road_closed,
            "summary": {"value": summary},
            "description": {"value": description},
            "typeDescription": {"value": type_description},
            "roadInfo": {"name": road_name},
            "severity": 3,
            "criticality": "major",
        },
        "location": {"shape": {"links": []}},
    }


def test_parse_incidente_road_closed_true_classifica_como_interdicao_total():
    inc = here_incidents._parse_incidente(  # noqa: SLF001
        _item(tipo="accident", road_closed=True, summary="Acidente com pista fechada")
    )

    assert inc is not None
    assert inc["categoria"] == "Interdição"
    assert inc["bloqueio_escopo"] == "total"
    assert inc["causa_detectada"] == "acidente"
    assert inc["road_closed_raw"] is True
    assert inc["road_closed"] is True


def test_parse_incidente_road_closure_classifica_como_interdicao_total():
    inc = here_incidents._parse_incidente(  # noqa: SLF001
        _item(tipo="roadClosure", summary="Trecho com fechamento")
    )

    assert inc is not None
    assert inc["categoria"] == "Interdição"
    assert inc["bloqueio_escopo"] == "total"
    assert inc["road_closed_raw"] is False
    assert inc["road_closed"] is True


def test_parse_incidente_lane_restriction_classifica_como_bloqueio_parcial():
    inc = here_incidents._parse_incidente(  # noqa: SLF001
        _item(tipo="laneRestriction", summary="Faixa interditada com transito fluindo")
    )

    assert inc is not None
    assert inc["categoria"] == "Bloqueio Parcial"
    assert inc["bloqueio_escopo"] == "parcial"
    assert inc["road_closed"] is False


def test_parse_incidente_accident_sem_fechamento_permanece_colisao():
    inc = here_incidents._parse_incidente(  # noqa: SLF001
        _item(tipo="accident", summary="Acidente com lentidao no trecho")
    )

    assert inc is not None
    assert inc["categoria"] == "Colisão"
    assert inc["bloqueio_escopo"] == "nenhum"
    assert inc["causa_detectada"] == "acidente"
    assert inc["road_closed"] is False


def test_parse_incidente_road_hazard_generico_nao_gera_interdicao():
    inc = here_incidents._parse_incidente(  # noqa: SLF001
        _item(tipo="roadHazard", summary="Objeto na pista")
    )

    assert inc is not None
    assert inc["categoria"] == "Ocorrência"
    assert inc["bloqueio_escopo"] == "nenhum"
    assert inc["causa_detectada"] == "risco"
    assert inc["road_closed"] is False


def test_parse_incidente_texto_bloqueio_total_forca_interdicao():
    inc = here_incidents._parse_incidente(  # noqa: SLF001
        _item(
            tipo="roadHazard",
            summary="Bloqueio total no trecho",
            description="Via totalmente bloqueada sem passagem",
        )
    )

    assert inc is not None
    assert inc["categoria"] == "Interdição"
    assert inc["bloqueio_escopo"] == "total"
    assert inc["road_closed_raw"] is False
    assert inc["road_closed"] is True
