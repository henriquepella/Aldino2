"""Logging estruturado simples (JSON opcional) para rastreabilidade (seção 40/42)."""
from __future__ import annotations

import logging
import sys

from app.core.config import settings

_CONFIGURED = False


def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    # evita "I/O operation on closed file" de threads de job após teardown de testes
    logging.raiseExceptions = False
    level = logging.DEBUG if settings.debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    for noisy in (
        "matplotlib", "PIL", "fiona", "rasterio", "numba",
        "python_multipart", "multipart", "httpx", "httpcore", "asyncio",
        "urllib3", "contextily", "requests", "mercantile", "rasterio._env",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
