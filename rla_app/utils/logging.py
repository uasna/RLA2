"""
RLA 2 — utils/logging.py
Configura el sistema de logging estándar de Python.
Debe llamarse una sola vez al arrancar la app.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(log_dir: Path | None = None, level: int = logging.DEBUG) -> None:
    """
    Configura handlers para consola y opcionalmente archivo.

    Args:
        log_dir: Si se pasa, escribe rla.log en esa carpeta.
        level:   Nivel mínimo de log. Default DEBUG.
    """
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%H:%M:%S",
    )

    root = logging.getLogger("rla")
    root.setLevel(level)
    root.handlers.clear()

    # Consola
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Archivo (opcional)
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / "rla.log", encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)
