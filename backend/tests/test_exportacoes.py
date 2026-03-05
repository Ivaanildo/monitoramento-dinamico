import pytest
from core import painel_service
from report.excel_simple import gerar_excel_visao_geral, gerar_csv_visao_geral, gerar_excel, gerar_csv

def test_geracao_painel_excel_estrutura():
    mock_resultados = [{
        "rota_id": "R01",
        "sigla": "BR-116",
        "nome": "O -> D",
        "trecho": "O / D",
        "status": "Normal",
        "ocorrencia": "",
        "relato": "",
        "hora_atualizacao": "2026",
        "confianca_pct": 100,
        "atraso_min": 0,
        "distancia_km": 100
    }]
    xlsx_bytes = gerar_excel_visao_geral(mock_resultados)
    assert isinstance(xlsx_bytes, bytes)
    assert len(xlsx_bytes) > 0

def test_geracao_painel_csv_estrutura():
    mock_resultados = [{
        "rota_id": "R01",
        "sigla": "BR-116",
        "nome": "O -> D",
        "trecho": "O / D",
        "status": "Normal",
        "ocorrencia": "",
        "relato": "",
        "hora_atualizacao": "2026",
        "confianca_pct": 100,
        "atraso_min": 0,
        "distancia_km": 100
    }]
    csv_str = gerar_csv_visao_geral(mock_resultados)
    assert isinstance(csv_str, str)
    assert "ID,Sigla (Rodovia),Nome,Trecho,Status" in csv_str
    assert "R01,BR-116,O -> D,O / D,Normal" in csv_str

def test_geracao_detalhado_excel_estrutura():
    mock_resultado = {
        "hub_origem": "O",
        "hub_destino": "D",
        "status": "Normal"
    }
    xlsx_bytes = gerar_excel(mock_resultado)
    assert isinstance(xlsx_bytes, bytes)
    assert len(xlsx_bytes) > 0

def test_geracao_detalhado_csv_estrutura():
    mock_resultado = {
        "hub_origem": "O",
        "hub_destino": "D",
        "status": "Normal"
    }
    csv_str = gerar_csv(mock_resultado)
    assert isinstance(csv_str, str)
    assert "Rota,Status,Atraso (min)" in csv_str
    assert "O → D,Normal" in csv_str
