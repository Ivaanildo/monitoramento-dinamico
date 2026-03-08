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


def test_incidente_com_rodovia_divergente_mantido_no_corridor():
    """No corridor, proximidade geométrica garante relevância — incidentes de
    rodovia não são rejeitados por código divergente."""
    inc = _incidente(descricao="Colisao na BR-381 km 10")
    filtrados = here_incidents._filtrar_relevancia_rodovia(  # noqa: SLF001
        [inc],
        ["BR-116"],
        "corridor",
    )

    assert filtrados == [inc]


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
