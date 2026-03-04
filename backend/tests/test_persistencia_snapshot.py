import pytest
import httpx
from unittest.mock import MagicMock

from core.painel_service import obter_painel_agregado
from storage.repository import salvar_snapshot_agregado
from storage.database import get_supabase, init_supabase

class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code
        self.text = "Error Text"
        
    def json(self):
        return self._json_data
        
    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://fake")
            raise httpx.HTTPStatusError(f"HTTP {self.status_code}", request=request, response=self)

def test_salvar_snapshot_agregado_sucesso(monkeypatch):
    mock_client = MagicMock()
    # first call is creating cycle
    mock_client.post.side_effect = [
        FakeResponse([{"id": 999}]), # ciclo response
        FakeResponse(None) # snapshot response
    ]
    monkeypatch.setattr("storage.repository.get_supabase", lambda: mock_client)
    
    resultados = [
        {"trecho": "A -> B", "sigla": "BR-116", "status": "Normal"}
    ]
    
    # Shouldn"t raise any exception
    salvar_snapshot_agregado(resultados)
    assert mock_client.post.call_count == 2

def test_salvar_snapshot_agregado_degradacao_silenciosa(monkeypatch):
    """Garante que exceptions HTTP no Supabase nao quebrem a aplicacao."""
    mock_client = MagicMock()
    mock_client.post.side_effect = httpx.ConnectError("Connection refused")
    monkeypatch.setattr("storage.repository.get_supabase", lambda: mock_client)
    
    resultados = [{"trecho": "A"}]
    # Deve falhar silenciosamente por causa do try/except
    salvar_snapshot_agregado(resultados)
    
def test_salvar_snapshot_agregado_erro_http(monkeypatch):
    """Garante que requests HTTP com 500 no Supabase sejam engolidas."""
    mock_client = MagicMock()
    mock_client.post.side_effect = [
        FakeResponse(None, status_code=500)
    ]
    monkeypatch.setattr("storage.repository.get_supabase", lambda: mock_client)
    
    resultados = [{"trecho": "A"}]
    # Deve ser engolido e apenas logado
    salvar_snapshot_agregado(resultados)
