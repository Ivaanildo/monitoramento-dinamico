from core import here_incidents


def _incidente(rodovia_afetada="", descricao=""):
    return {
        "rodovia_afetada": rodovia_afetada,
        "descricao": descricao,
    }


def test_incidente_sem_br_explicita_e_rejeitado_no_corridor():
    filtrados = here_incidents._filtrar_relevancia_rodovia(  # noqa: SLF001
        [_incidente(descricao="entre av amazonas e r santa maria")],
        ["BR-116"],
        "corridor",
    )

    assert filtrados == []


def test_incidente_sem_br_explicita_e_rejeitado_no_bbox():
    filtrados = here_incidents._filtrar_relevancia_rodovia(  # noqa: SLF001
        [_incidente(descricao="entre av amazonas e r santa maria")],
        ["BR-116"],
        "bbox",
    )

    assert filtrados == []


def test_rota_multi_br_aceita_incidente_com_codigo_compativel():
    inc = _incidente(descricao="Acidente no km 22 da BR-101")

    filtrados = here_incidents._filtrar_relevancia_rodovia(  # noqa: SLF001
        [inc],
        ["BR-116", "BR-101"],
        "corridor",
    )

    assert filtrados == [inc]


def test_incidente_com_rodovia_divergente_rejeitado_no_corridor():
    """No corridor, incidentes com código de rodovia divergente são descartados."""
    filtrados = here_incidents._filtrar_relevancia_rodovia(  # noqa: SLF001
        [_incidente(descricao="Colisao na BR-381 km 10")],
        ["BR-116"],
        "corridor",
    )
    assert filtrados == []


def test_incidente_sem_codigo_mantido_e_tagueado_no_corridor():
    """Incidente sem código de rodovia é mantido no corridor mas tagueado como sem_codigo."""
    inc = _incidente(rodovia_afetada="Anel Rodoviário", descricao="Interdição total")
    filtrados = here_incidents._filtrar_relevancia_rodovia(  # noqa: SLF001
        [inc],
        ["BR-381"],
        "corridor",
    )
    assert len(filtrados) == 1
    assert filtrados[0]["match_tipo"] == "sem_codigo"


def test_incidente_compativel_tagueado_no_corridor():
    """Incidente com código de rodovia compatível recebe match_tipo 'compatível'."""
    inc = _incidente(descricao="Acidente no km 22 da BR-381")
    filtrados = here_incidents._filtrar_relevancia_rodovia(  # noqa: SLF001
        [inc],
        ["BR-381"],
        "corridor",
    )
    assert len(filtrados) == 1
    assert filtrados[0]["match_tipo"] == "compatível"


def test_incidente_com_rodovia_divergente_e_rejeitado_no_bbox():
    """No bbox, incidentes com código de rodovia divergente ainda são rejeitados."""
    filtrados = here_incidents._filtrar_relevancia_rodovia(  # noqa: SLF001
        [_incidente(descricao="Colisao na BR-381 km 10")],
        ["BR-116"],
        "bbox",
    )

    assert filtrados == []


def test_sem_rodovia_logica_reconhecivel_mantem_comportamento_legado():
    inc = _incidente(descricao="entre av amazonas e r santa maria")

    filtrados = here_incidents._filtrar_relevancia_rodovia(  # noqa: SLF001
        [inc],
        ["Trecho logistica principal"],
        "corridor",
    )

    assert filtrados == [inc]
