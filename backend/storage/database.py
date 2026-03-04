import logging
import httpx

logger = logging.getLogger(__name__)

_supabase_http_client: httpx.Client | None = None
_supabase_url: str = ""

def init_supabase(config: dict) -> httpx.Client | None:
    """Inicializa e retorna o cliente HTTP configurado para Supabase REST API."""
    global _supabase_http_client, _supabase_url
    if _supabase_http_client is not None:
        return _supabase_http_client

    supabase_config = config.get("supabase", {})
    url = supabase_config.get("url")
    key = supabase_config.get("key")

    if not url or not key:
        logger.warning("Credenciais Supabase (url ou key) nao encontradas na configuracao carregada.")
        return None

    try:
        _supabase_url = f"{str(url).rstrip('/')}/rest/v1"
        _supabase_http_client = httpx.Client(
            base_url=_supabase_url,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Profile": "public",
                "Prefer": "return=representation"
            },
            timeout=10.0
        )
        logger.info("Cliente HTTP Supabase inicializado com sucesso.")
        return _supabase_http_client
    except Exception as e:
        logger.error(f"Erro ao inicializar HTTTP Supabase: {e}")
        return None

def get_supabase() -> httpx.Client | None:
    """Retorna o cliente HTTP já inicializado ou None."""
    global _supabase_http_client
    return _supabase_http_client
