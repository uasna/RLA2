"""
RLA 2 — utils/file_stability.py
Espera a que un archivo termine de escribirse antes de procesarlo.
Solo stdlib. Sin dependencias externas.
"""
from __future__ import annotations

import time
from pathlib import Path


def wait_for_file_stability(
    path: Path,
    checks: int = 2,
    interval_seconds: float = 1.0,
    timeout_seconds: float = 15.0,
) -> bool:
    """
    Espera a que `path` deje de cambiar en tamaño y fecha de modificación.

    Returns:
        True  — archivo estable tras `checks` comprobaciones consecutivas.
        False — timeout alcanzado o archivo inválido.
    """
    deadline = time.monotonic() + timeout_seconds
    consecutive = 0
    last_size: int | None = None
    last_mtime: float | None = None

    while time.monotonic() < deadline:
        if not path.is_file():
            consecutive = 0
            last_size = last_mtime = None
            time.sleep(interval_seconds)
            continue

        try:
            stat = path.stat()
            size, mtime = stat.st_size, stat.st_mtime
        except OSError:
            consecutive = 0
            time.sleep(interval_seconds)
            continue

        if size == last_size and mtime == last_mtime:
            consecutive += 1
            if consecutive >= checks:
                return True
        else:
            consecutive = 1          # la muestra actual cuenta como primera

        last_size, last_mtime = size, mtime
        time.sleep(interval_seconds)

    return False