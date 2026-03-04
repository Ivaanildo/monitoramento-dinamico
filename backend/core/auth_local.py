"""Autenticacao local temporaria.

Responsavel por gerenciar sessoes locais via cookie
antes da migracao para Supabase Auth.
"""
import hashlib
import hmac
import logging
import time

from fastapi import HTTPException, Request, Response

logger = logging.getLogger(__name__)

SESSION_COOKIE_NAME = "projeto_zero_session"
TOKEN_MAX_AGE_SECONDS = 86400  # 24 hours


def is_auth_enabled(config: dict) -> bool:
    """Verifica se a autenticacao local esta ativada."""
    return config.get("auth_local", {}).get("enabled", False)


def is_auth_blocked(config: dict) -> bool:
    """Indica que a auth foi bloqueada por configuracao insegura."""
    return bool(config.get("auth_local", {}).get("blocked_due_to_placeholders", False))


def get_credentials(config: dict) -> tuple[str, str]:
    """Retorna username e password locais configurados."""
    auth_config = config.get("auth_local", {})
    return (
        auth_config.get("username", "operacao"),
        auth_config.get("password", "definir_localmente")
    )


def is_cookie_secure(config: dict) -> bool:
    """Retorna se o cookie deve ser marcado como Secure."""
    return bool(config.get("auth_local", {}).get("cookie_secure", False))


def _compute_hmac(username: str, timestamp: str, secret: str) -> str:
    """Gera HMAC-SHA256 do payload `username|timestamp` usando o secret."""
    message = f"{username}|{timestamp}"
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def criar_sessao(response: Response, username: str, config: dict):
    """Cria cookie de sessao com token HMAC-assinado e HTTP-only."""
    auth_config = config.get("auth_local", {})
    secret = auth_config.get("session_secret", "trocar-em-dev")

    timestamp = str(int(time.time()))
    signature = _compute_hmac(username, timestamp, secret)
    session_token = f"{username}|{timestamp}|{signature}"

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=is_cookie_secure(config),
    )

def limpar_sessao(response: Response, config: dict | None = None):
    """Remove cookie de sessao."""
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=is_cookie_secure(config or {}),
    )


def validar_sessao(request: Request, config: dict) -> str:
    """Valida cookie de sessao e retorna o username.

    Lanca HTTPException 401 caso falhe ou nao exista.
    """
    if is_auth_blocked(config):
        raise HTTPException(
            status_code=503,
            detail="Auth local bloqueada por configuracao insegura.",
        )

    if not is_auth_enabled(config):
        return "desabilitado"

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Nao autorizado. Faca login.")

    auth_config = config.get("auth_local", {})
    secret = auth_config.get("session_secret", "trocar-em-dev")

    try:
        parts = token.split("|")
        if len(parts) != 3:
            raise ValueError("Formato de token invalido")

        username, timestamp, provided_sig = parts

        # Verificar HMAC
        expected_sig = _compute_hmac(username, timestamp, secret)
        if not hmac.compare_digest(provided_sig, expected_sig):
            raise ValueError("Assinatura HMAC invalida")

        # Verificar expiração
        token_age = int(time.time()) - int(timestamp)
        if token_age > TOKEN_MAX_AGE_SECONDS:
            raise ValueError("Token expirado")
        if token_age < 0:
            raise ValueError("Timestamp futuro")

        return username
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Sessao invalida detectada: {e}")
        raise HTTPException(status_code=401, detail="Sessao invalida ou expirada.")


def verificar_dependencia_auth(request: Request):
    """Dependencia FastAPI basica. Injetamos _config via closure no app.py."""
    pass  # Sera chamada direto no app.py passando o _config
