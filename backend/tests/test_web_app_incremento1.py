import pytest
from fastapi.testclient import TestClient
from web import app as web_app
from web.app import app, verificar_autenticacao

client = TestClient(app)

# Inject explicitly a test config 
test_config_auth_enabled = {
    "auth_local": {
        "enabled": True,
        "username": "operacao",
        "password": "definir_localmente",
        "session_secret": "secret_de_teste"
    }
}
test_config_auth_disabled = {
    "auth_local": {
        "enabled": False,
    }
}
test_config_auth_blocked = {
    "auth_local": {
        "enabled": False,
        "blocked_due_to_placeholders": True,
    }
}

@pytest.fixture(autouse=True)
def _reset_config():
    # Reset config to disabled before each test unless overridden, maintaining reference
    web_app._config.clear()
    web_app._config.update(test_config_auth_disabled)
    app.dependency_overrides = {}
    yield

def _mock_auth():
    return "operacao"

def test_healthz_publico():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_rotas_corporativas():
    response = client.get("/rotas")
    assert response.status_code == 200
    dados = response.json()
    assert "rotas" in dados
    rotas = dados["rotas"]
    assert len(rotas) == 20
    assert "id" in rotas[0]
    assert "origem" in rotas[0]

def test_get_painel_agregado():
    response = client.get("/painel")
    assert response.status_code == 200
    dados = response.json()
    assert "total_rotas" in dados
    assert "resultados" in dados
    assert "consultado_em" in dados

def test_login_logout():
    web_app._config.clear()
    web_app._config.update(test_config_auth_enabled)
    # Attempt login with correct default credentials defined in yaml
    payload = {"username": "operacao", "password": "definir_localmente"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    assert "set-cookie" in response.headers
    cookie_header = response.headers["set-cookie"]
    assert "projeto_zero_session=" in cookie_header
    # Cookie should have HMAC format: username|ts|sig (3 parts)
    cookie_val = cookie_header.split("projeto_zero_session=")[1].split(";")[0]
    assert cookie_val.count("|") == 2, f"Expected HMAC format with 3 parts, got: {cookie_val}"
    # Secret must NOT appear in cookie
    assert "secret_de_teste" not in cookie_val
    
    # Attempt login with wrong credentials
    payload = {"username": "operacao", "password": "wrong"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    # cookie should be cleared
    if "set-cookie" in response.headers:
        assert 'projeto_zero_session=""' in response.headers["set-cookie"] or "Max-Age=0" in response.headers["set-cookie"]

def test_auth_session_check_disabled():
    response = client.get("/auth/session")
    assert response.status_code == 200
    assert response.json()["authenticated"] is True

def test_auth_session_check_enabled_no_cookie():
    web_app._config.clear()
    web_app._config.update(test_config_auth_enabled)
    response = client.get("/auth/session")
    assert response.status_code == 401
    assert response.json()["authenticated"] is False


def test_auth_session_check_blocked():
    web_app._config.clear()
    web_app._config.update(test_config_auth_blocked)
    response = client.get("/auth/session")
    assert response.status_code == 503
    assert response.json() == {"authenticated": False, "auth_blocked": True}

def test_get_rotas_corporativas_auth():
    web_app._config.clear()
    web_app._config.update(test_config_auth_enabled)
    app.dependency_overrides[verificar_autenticacao] = _mock_auth
    response = client.get("/rotas")
    assert response.status_code == 200
    assert len(response.json()["rotas"]) == 20

def test_get_painel_agregado_auth():
    web_app._config.clear()
    web_app._config.update(test_config_auth_enabled)
    app.dependency_overrides[verificar_autenticacao] = _mock_auth
    response = client.get("/painel")
    assert response.status_code == 200
    assert "total_rotas" in response.json()

def test_obter_rota_por_id_auth():
    web_app._config.clear()
    web_app._config.update(test_config_auth_enabled)
    app.dependency_overrides[verificar_autenticacao] = _mock_auth
    response = client.get("/rotas/R01")
    assert response.status_code == 200
    assert response.json()["id"] == "R01"

def test_rota_nao_encontrada():
    web_app._config.clear()
    web_app._config.update(test_config_auth_enabled)
    app.dependency_overrides[verificar_autenticacao] = _mock_auth
    response = client.get("/rotas/R99")
    assert response.status_code == 404


def test_favoritos_requer_auth():
    web_app._config.clear()
    web_app._config.update(test_config_auth_enabled)
    app.dependency_overrides = {}
    response = client.get("/favoritos")
    assert response.status_code == 401


def test_favoritos_com_auth():
    web_app._config.clear()
    web_app._config.update(test_config_auth_enabled)
    app.dependency_overrides[verificar_autenticacao] = _mock_auth
    response = client.get("/favoritos")
    assert response.status_code == 200
    assert "favoritos" in response.json()


def test_favoritos_bloqueado_quando_placeholder_force_disable():
    web_app._config.clear()
    web_app._config.update(test_config_auth_blocked)
    app.dependency_overrides = {}
    response = client.get("/favoritos")
    assert response.status_code == 503


def test_cache_delete_requer_auth():
    web_app._config.clear()
    web_app._config.update(test_config_auth_enabled)
    app.dependency_overrides = {}
    response = client.delete("/cache")
    assert response.status_code == 401


def test_cache_info_requer_auth():
    web_app._config.clear()
    web_app._config.update(test_config_auth_enabled)
    app.dependency_overrides = {}
    response = client.get("/cache/info")
    assert response.status_code == 401


def test_login_retorna_503_quando_auth_bloqueada():
    web_app._config.clear()
    web_app._config.update(test_config_auth_blocked)
    payload = {"username": "operacao", "password": "qualquer"}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 503
