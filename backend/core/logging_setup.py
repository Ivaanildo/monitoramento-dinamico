"""Configuração central de logging do backend (console-only)."""
import logging
import sys
import threading

_LOCK = threading.Lock()
_CONFIGURADO = False


def setup_logging() -> None:
    """Configura logging global de forma idempotente."""
    global _CONFIGURADO

    if _CONFIGURADO:
        logging.getLogger().setLevel(logging.INFO)
        return

    with _LOCK:
        if _CONFIGURADO:
            logging.getLogger().setLevel(logging.INFO)
            return

        # Garante UTF-8 no stdout (necessário no Windows com Python 3.14+)
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
            stream=sys.stdout,
            force=False,
        )
        logging.getLogger().setLevel(logging.INFO)
        _CONFIGURADO = True
