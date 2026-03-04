"""Cache in-memory com TTL por chave."""
import threading
import time


class TTLCache:
    """Cache thread-safe com expiração por tempo (TTL)."""

    def __init__(self, ttl_segundos: int = 300):
        self._ttl = ttl_segundos
        self._store: dict = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value) -> None:
        with self._lock:
            self._store[key] = (value, time.monotonic() + self._ttl)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def purge_expired(self) -> int:
        """Remove entradas expiradas. Retorna quantidade removida."""
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]
        return len(expired)

    def size(self) -> int:
        with self._lock:
            return len(self._store)


# Cache global compartilhado pela aplicação (TTL configurável via consultor)
_cache_global: TTLCache | None = None


def get_cache(ttl_segundos: int = 300) -> TTLCache:
    global _cache_global
    if _cache_global is None:
        _cache_global = TTLCache(ttl_segundos)
    return _cache_global
