"""Testes para: log HTTP detalhado e bbox fallback quando corridor retorna 400."""
import logging
from unittest.mock import MagicMock, patch

import pytest
import requests

from core import here_incidents


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_http_error(status_code: int, body: dict | str) -> requests.exceptions.HTTPError:
    """Cria um HTTPError com response mockada."""
    response = MagicMock()
    response.status_code = status_code
    if isinstance(body, dict):
        response.json.return_value = body
        response.text = str(body)
    else:
        response.json.side_effect = ValueError("not json")
        response.text = body
    err = requests.exceptions.HTTPError(response=response)
    return err


def _sessao_que_lanca(error: Exception):
    """Retorna um mock de sessão cujo .get() lança o erro dado."""
    sess = MagicMock()
    sess.get.return_value.__enter__ = lambda s: s
    sess.get.side_effect = error
    return sess


# ── _consultar_incidents_zones ───────────────────────────────────────────────


def test_incidents_loga_status_e_body_quando_http_400(caplog):
    body = {"title": "Bad Request", "status": 400, "cause": "invalid corridor"}
    http_err = _make_http_error(400, body)

    with patch.object(here_incidents, "_get_sessao") as mock_sess:
        mock_sess.return_value.get.return_value.raise_for_status.side_effect = http_err

        with caplog.at_level(logging.WARNING, logger="core.here_incidents"):
            result = here_incidents._consultar_incidents_zones("KEY", ["corridor_zone"])  # noqa: SLF001

    assert result == []
    assert "HTTP 400" in caplog.text
    assert "Bad Request" in caplog.text


def test_incidents_loga_status_quando_body_nao_e_json(caplog):
    http_err = _make_http_error(403, "Forbidden plain text")

    with patch.object(here_incidents, "_get_sessao") as mock_sess:
        mock_sess.return_value.get.return_value.raise_for_status.side_effect = http_err

        with caplog.at_level(logging.WARNING, logger="core.here_incidents"):
            result = here_incidents._consultar_incidents_zones("KEY", ["zone"])  # noqa: SLF001

    assert result == []
    assert "HTTP 403" in caplog.text


def test_incidents_retorna_vazio_sem_travar_quando_request_exception(caplog):
    conn_err = requests.exceptions.ConnectionError("timeout")

    with patch.object(here_incidents, "_get_sessao") as mock_sess:
        mock_sess.return_value.get.side_effect = conn_err

        with caplog.at_level(logging.WARNING, logger="core.here_incidents"):
            result = here_incidents._consultar_incidents_zones("KEY", ["zone"])  # noqa: SLF001

    assert result == []


# ── _consultar_flow_zones ────────────────────────────────────────────────────


def test_flow_loga_status_e_body_quando_http_400(caplog):
    body = {"title": "Bad Request", "status": 400}
    http_err = _make_http_error(400, body)

    with patch.object(here_incidents, "_get_sessao") as mock_sess:
        mock_sess.return_value.get.return_value.raise_for_status.side_effect = http_err

        with caplog.at_level(logging.WARNING, logger="core.here_incidents"):
            result = here_incidents._consultar_flow_zones("KEY", ["corridor_zone"])  # noqa: SLF001

    assert result == []
    assert "HTTP 400" in caplog.text
    assert "Bad Request" in caplog.text


def test_flow_loga_status_quando_body_nao_e_json(caplog):
    http_err = _make_http_error(401, "Unauthorized")

    with patch.object(here_incidents, "_get_sessao") as mock_sess:
        mock_sess.return_value.get.return_value.raise_for_status.side_effect = http_err

        with caplog.at_level(logging.WARNING, logger="core.here_incidents"):
            result = here_incidents._consultar_flow_zones("KEY", ["zone"])  # noqa: SLF001

    assert result == []
    assert "HTTP 401" in caplog.text


# ── bbox fallback no bloco principal ─────────────────────────────────────────


def _patch_consultar(api_key, origem, destino, *, corridor_inc, corridor_flow,
                     bbox_inc, bbox_flow, route_pts=None):
    """
    Executa here_incidents.consultar() com mocks controlados:
    - Geocode retorna coordenadas fixas
    - Routing retorna route_pts (ou lista vazia para forçar bbox direto)
    - encode_corridor retorna string não-vazia
    - _consultar_incidents_zones e _consultar_flow_zones retornam valores
      diferentes na 1ª chamada (corridor) e na 2ª (bbox)
    """
    coords = (-23.0, -46.0)
    call_count_inc = {"n": 0}
    call_count_flow = {"n": 0}

    def fake_incidents(key, zones):
        call_count_inc["n"] += 1
        return corridor_inc if call_count_inc["n"] == 1 else bbox_inc

    def fake_flow(key, zones):
        call_count_flow["n"] += 1
        return corridor_flow if call_count_flow["n"] == 1 else bbox_flow

    with (
        patch.object(here_incidents, "_parse_ou_geocode", return_value=coords),
        patch.object(here_incidents, "_obter_polyline_rota",
                     return_value=route_pts if route_pts is not None else [coords, coords]),
        patch("core.here_incidents.encode_corridor", return_value="corridor_encoded"),
        patch("core.here_incidents.pts_to_geojson_line", return_value=None),
        patch.object(here_incidents, "_consultar_incidents_zones", side_effect=fake_incidents),
        patch.object(here_incidents, "_consultar_flow_zones", side_effect=fake_flow),
        patch.object(here_incidents, "_gerar_bboxes_fallback",
                     return_value=["bbox_zone"]) as mock_bbox,
        patch.object(here_incidents, "_filtrar_relevancia_rodovia",
                     side_effect=lambda incs, *a, **kw: incs),
        patch.object(here_incidents, "_filtrar_relevancia_bbox",
                     side_effect=lambda incs, *a, **kw: incs),
    ):
        resultado = here_incidents.consultar("KEY", origem, destino)
        return resultado, mock_bbox


def test_bbox_fallback_ativado_quando_corridor_retorna_vazio(caplog):
    inc_bbox = [{"tipo": "accident", "descricao": "Acidente via bbox"}]

    with caplog.at_level(logging.INFO, logger="core.here_incidents"):
        resultado, mock_bbox = _patch_consultar(
            "KEY", "origem", "destino",
            corridor_inc=[],
            corridor_flow=[],
            bbox_inc=inc_bbox,
            bbox_flow=[],
        )

    assert resultado["metodo_busca"] == "bbox_fallback"
    assert "bbox fallback" in caplog.text.lower()
    mock_bbox.assert_called_once()


def test_bbox_fallback_nao_ativado_quando_corridor_retorna_dados():
    inc_corridor = [{"tipo": "accident", "descricao": "Acidente via corridor"}]

    resultado, mock_bbox = _patch_consultar(
        "KEY", "origem", "destino",
        corridor_inc=inc_corridor,
        corridor_flow=[],
        bbox_inc=[],
        bbox_flow=[],
    )

    assert resultado["metodo_busca"] == "corridor"
    mock_bbox.assert_not_called()


def test_bbox_fallback_nao_ativado_quando_corridor_tem_so_flow():
    flow_corridor = [{"speed": 60}]

    resultado, mock_bbox = _patch_consultar(
        "KEY", "origem", "destino",
        corridor_inc=[],
        corridor_flow=flow_corridor,
        bbox_inc=[],
        bbox_flow=[],
    )

    # flow retornou dado → não deve acionar fallback
    assert resultado["metodo_busca"] == "corridor"
    mock_bbox.assert_not_called()


def test_bbox_fallback_nao_ativado_quando_ja_usa_bbox_direto():
    """Quando routing falha (route_pts=[]), usa bbox direto; fallback não deve dobrar."""
    resultado, mock_bbox = _patch_consultar(
        "KEY", "origem", "destino",
        corridor_inc=[],
        corridor_flow=[],
        bbox_inc=[],
        bbox_flow=[],
        route_pts=[],           # força usar_corridor=False desde o início
    )

    # metodo_busca deve ser "bbox" (não "bbox_fallback")
    assert resultado["metodo_busca"] == "bbox"
    # _gerar_bboxes_fallback é chamada 1x pelo bloco de estratégia, não pelo fallback
    assert mock_bbox.call_count == 1
