"""Shared configuration loader for the backend runtime.

Loads YAML configuration and applies environment overrides so the web app,
CLI, and worker all share the same source of truth.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"
_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}

# Known placeholder values that must NOT be used in production
_PLACEHOLDER_SECRETS = {"trocar-em-producao", "trocar-em-dev", "definir_localmente"}


def _parse_bool(value) -> bool | None:
    """Normalize common string and bool representations."""
    if isinstance(value, bool):
        return value
    if value is None:
        return None

    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return None


def _ensure_section(config: dict, section_name: str) -> dict:
    section = config.get(section_name)
    if not isinstance(section, dict):
        section = {}
        config[section_name] = section
    return section


def load_config(config_path: str | Path | None = None) -> dict:
    """Load the config file and apply env-first overrides."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError(f"Config invalido: {path} (deve ser .yaml/.yml)")

    config: dict = {}
    if path.exists():
        with open(path, encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file) or {}

    config["__config_path"] = str(path.resolve())

    google = _ensure_section(config, "google")
    here = _ensure_section(config, "here")
    auth_local = _ensure_section(config, "auth_local")
    supabase = _ensure_section(config, "supabase")
    auth_local["blocked_due_to_placeholders"] = False

    google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if google_api_key:
        google["api_key"] = google_api_key

    here_api_key = os.getenv("HERE_API_KEY")
    if here_api_key:
        here["api_key"] = here_api_key

    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        supabase["url"] = supabase_url

    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if supabase_key:
        supabase["key"] = supabase_key

    auth_enabled = _parse_bool(os.getenv("AUTH_LOCAL_ENABLED"))
    if auth_enabled is not None:
        auth_local["enabled"] = auth_enabled
    else:
        auth_local["enabled"] = _parse_bool(auth_local.get("enabled"))
        if auth_local["enabled"] is None:
            auth_local["enabled"] = False

    auth_username = os.getenv("AUTH_LOCAL_USERNAME")
    if auth_username:
        auth_local["username"] = auth_username

    auth_password = os.getenv("AUTH_LOCAL_PASSWORD")
    if auth_password:
        auth_local["password"] = auth_password

    auth_session_secret = os.getenv("AUTH_LOCAL_SESSION_SECRET")
    if auth_session_secret:
        auth_local["session_secret"] = auth_session_secret

    auth_cookie_secure = _parse_bool(os.getenv("AUTH_COOKIE_SECURE"))
    if auth_cookie_secure is not None:
        auth_local["cookie_secure"] = auth_cookie_secure
    else:
        auth_local["cookie_secure"] = _parse_bool(auth_local.get("cookie_secure"))
        if auth_local["cookie_secure"] is None:
            auth_local["cookie_secure"] = False

    # --- Placeholder guard (SBP-002) ---
    if auth_local.get("enabled"):
        secret = auth_local.get("session_secret", "")
        password = auth_local.get("password", "")
        offenders = []
        if secret in _PLACEHOLDER_SECRETS:
            offenders.append(f"session_secret='{secret}'")
        if password in _PLACEHOLDER_SECRETS:
            offenders.append(f"password='{password}'")
        if offenders:
            logger.error(
                "AUTH DESABILITADA AUTOMATICAMENTE: credenciais placeholder "
                "detectadas (%s). Defina valores reais via env vars "
                "AUTH_LOCAL_SESSION_SECRET / AUTH_LOCAL_PASSWORD antes de "
                "habilitar auth_local.",
                ", ".join(offenders),
            )
            auth_local["enabled"] = False
            auth_local["blocked_due_to_placeholders"] = True

    return config
