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

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
            stream=sys.stdout,
            force=False,
        )
        logging.getLogger().setLevel(logging.INFO)
        _CONFIGURADO = True
