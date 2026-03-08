import pytest
from core.painel_service import converter_para_resumo_painel

def test_converter_para_resumo_painel():
    rota_corp = {
        "id": "R01",
        "hub_origem": "Sao Paulo",
        "hub_destino": "Cabo",
        "rodovia_logica": ["BR-116", "BR-101"]
    }
    resultado_detalhado = {
        "status": "Intenso",
        "atraso_min": 15,
        "confianca_pct": 90,
        "distancia_km": 2565.7,
        "incidente_principal": {
            "categoria": "Acidente",
            "descricao": "Colisao na via"
        },
        "consultado_em": "2026-03-03T12:00:00Z"
    }

    resumo = converter_para_resumo_painel(rota_corp, resultado_detalhado)

    assert resumo["rota_id"] == "R01"
    assert resumo["sigla"] == "BR-116 / BR-101"
    assert resumo["nome"] == "Sao Paulo -> Cabo"
    assert resumo["trecho"] == "Sao Paulo / Cabo"
    assert resumo["status"] == "Intenso"
    assert resumo["ocorrencia"] == "Acidente"
    assert "Acidente em BR-116 / BR-101" in resumo["relato"]
    assert "Atraso 15 min" in resumo["relato"]
    assert resumo["hora_atualizacao"] == "2026-03-03T12:00:00Z"
    assert resumo["confianca_pct"] == 90
    assert resumo["atraso_min"] == 15
    assert resumo["distancia_km"] == 2565.7

def test_converter_para_resumo_painel_fallback():
    rota_corp = {"id": "R02"}
    resultado_detalhado = {}

    resumo = converter_para_resumo_painel(rota_corp, resultado_detalhado)

    assert resumo["rota_id"] == "R02"
    assert resumo["sigla"] == "Desconhecida"
    assert resumo["status"] == "Erro"
    assert resumo["ocorrencia"] == ""
    assert "fluxo livre" in resumo["relato"]
    assert resumo["confianca_pct"] == 0
    assert resumo["atraso_min"] == 0
