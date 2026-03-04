import hashlib
import hmac as hmac_mod
import time

import pytest
from fastapi import Response
from fastapi import HTTPException
from unittest.mock import MagicMock
from core import auth_local

_config_disabled = {"auth_local": {"enabled": False}}
_config_enabled = {
    "auth_local": {
        "enabled": True,
        "username": "operacao",
        "password": "definir_localmente",
        "session_secret": "test_secret"
    }
}
_config_blocked = {
    "auth_local": {
        "enabled": False,
        "blocked_due_to_placeholders": True,
    }
}


def _make_token(username: str, secret: str, timestamp: int | None = None) -> str:
    """Helper: build a valid HMAC-signed session token."""
    ts = str(timestamp if timestamp is not None else int(time.time()))
    sig = hmac_mod.new(
        secret.encode("utf-8"),
        f"{username}|{ts}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{username}|{ts}|{sig}"


def test_is_auth_enabled():
    assert auth_local.is_auth_enabled(_config_enabled) is True
    assert auth_local.is_auth_enabled(_config_disabled) is False


def test_get_credentials():
    user, pwd = auth_local.get_credentials(_config_enabled)
    assert user == "operacao"
    assert pwd == "definir_localmente"


def test_validar_sessao_disabled():
    mock_req = MagicMock()
    # Should skip validation
    username = auth_local.validar_sessao(mock_req, _config_disabled)
    assert username == "desabilitado"


def test_validar_sessao_no_cookie():
    mock_req = MagicMock()
    mock_req.cookies = {}
    with pytest.raises(HTTPException):
        auth_local.validar_sessao(mock_req, _config_enabled)


def test_validar_sessao_bloqueada_por_placeholder():
    mock_req = MagicMock()
    mock_req.cookies = {}
    with pytest.raises(HTTPException) as exc_info:
        auth_local.validar_sessao(mock_req, _config_blocked)
    assert exc_info.value.status_code == 503


def test_validar_sessao_invalid_token():
    mock_req = MagicMock()
    mock_req.cookies = {auth_local.SESSION_COOKIE_NAME: "operacao|123|bad_hmac"}
    with pytest.raises(HTTPException):
        auth_local.validar_sessao(mock_req, _config_enabled)


def test_validar_sessao_valid_token():
    token = _make_token("operacao", "test_secret")
    mock_req = MagicMock()
    mock_req.cookies = {auth_local.SESSION_COOKIE_NAME: token}
    username = auth_local.validar_sessao(mock_req, _config_enabled)
    assert username == "operacao"


def test_validar_sessao_expired_token():
    """Token older than TOKEN_MAX_AGE_SECONDS should be rejected."""
    expired_ts = int(time.time()) - auth_local.TOKEN_MAX_AGE_SECONDS - 10
    token = _make_token("operacao", "test_secret", timestamp=expired_ts)
    mock_req = MagicMock()
    mock_req.cookies = {auth_local.SESSION_COOKIE_NAME: token}
    with pytest.raises(HTTPException):
        auth_local.validar_sessao(mock_req, _config_enabled)


def test_validar_sessao_malformed_token():
    """Token without 3 parts should be rejected."""
    mock_req = MagicMock()
    mock_req.cookies = {auth_local.SESSION_COOKIE_NAME: "only_one_part"}
    with pytest.raises(HTTPException):
        auth_local.validar_sessao(mock_req, _config_enabled)


def test_criar_sessao_default_sem_secure():
    response = Response()
    auth_local.criar_sessao(response, "operacao", _config_enabled)

    assert "set-cookie" in response.headers
    assert "Secure" not in response.headers["set-cookie"]
    # Cookie should contain 3 pipe-separated parts (username|ts|hmac)
    cookie_value = response.headers["set-cookie"].split("=", 1)[1].split(";")[0]
    assert cookie_value.count("|") == 2
    # Secret should NOT appear in cookie
    assert "test_secret" not in cookie_value


def test_criar_sessao_secure_quando_habilitado():
    response = Response()
    config = {
        "auth_local": {
            "enabled": True,
            "username": "operacao",
            "password": "definir_localmente",
            "session_secret": "test_secret",
            "cookie_secure": True,
        }
    }

    auth_local.criar_sessao(response, "operacao", config)

    assert "Secure" in response.headers["set-cookie"]


def test_cookie_nao_expoe_secret():
    """Ensure the session_secret is NEVER present in the cookie value."""
    response = Response()
    auth_local.criar_sessao(response, "operacao", _config_enabled)
    raw_cookie = response.headers["set-cookie"]
    assert "test_secret" not in raw_cookie
