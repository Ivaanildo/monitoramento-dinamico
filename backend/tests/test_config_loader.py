from pathlib import Path

from core.config_loader import load_config


def test_load_config_aplica_overrides_de_ambiente(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
google:
  api_key: "arquivo-google"
here:
  api_key: "arquivo-here"
auth_local:
  enabled: false
  username: "arquivo-user"
  password: "arquivo-pass"
  session_secret: "arquivo-secret"
  cookie_secure: false
supabase:
  url: "https://arquivo.supabase.co"
  key: "arquivo-key"
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "env-google")
    monkeypatch.setenv("HERE_API_KEY", "env-here")
    monkeypatch.setenv("SUPABASE_URL", "https://env.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "env-service-role")
    monkeypatch.setenv("AUTH_LOCAL_ENABLED", "true")
    monkeypatch.setenv("AUTH_LOCAL_USERNAME", "env-user")
    monkeypatch.setenv("AUTH_LOCAL_PASSWORD", "env-pass")
    monkeypatch.setenv("AUTH_LOCAL_SESSION_SECRET", "env-secret")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")

    config = load_config(config_path)

    assert config["google"]["api_key"] == "env-google"
    assert config["here"]["api_key"] == "env-here"
    assert config["supabase"]["url"] == "https://env.supabase.co"
    assert config["supabase"]["key"] == "env-service-role"
    assert config["auth_local"]["enabled"] is True
    assert config["auth_local"]["username"] == "env-user"
    assert config["auth_local"]["password"] == "env-pass"
    assert config["auth_local"]["session_secret"] == "env-secret"
    assert config["auth_local"]["cookie_secure"] is True
    assert config["auth_local"]["blocked_due_to_placeholders"] is False
    assert config["__config_path"] == str(Path(config_path).resolve())


def test_load_config_usa_fallback_legado_e_normaliza_booleanos(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
auth_local:
  enabled: "yes"
  cookie_secure: "off"
supabase:
  url: "https://arquivo.supabase.co"
  key: ""
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_KEY", "legacy-key")
    monkeypatch.delenv("AUTH_LOCAL_ENABLED", raising=False)
    monkeypatch.delenv("AUTH_COOKIE_SECURE", raising=False)

    config = load_config(config_path)

    assert config["supabase"]["key"] == "legacy-key"
    assert config["auth_local"]["enabled"] is True
    assert config["auth_local"]["cookie_secure"] is False
    assert config["auth_local"]["blocked_due_to_placeholders"] is False


def test_load_config_bloqueia_auth_com_placeholders(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
auth_local:
  enabled: true
  password: "definir_localmente"
  session_secret: "trocar-em-producao"
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.delenv("AUTH_LOCAL_ENABLED", raising=False)
    monkeypatch.delenv("AUTH_LOCAL_PASSWORD", raising=False)
    monkeypatch.delenv("AUTH_LOCAL_SESSION_SECRET", raising=False)

    config = load_config(config_path)

    assert config["auth_local"]["enabled"] is False
    assert config["auth_local"]["blocked_due_to_placeholders"] is True
