"""
RLA 2 — storage/replay_fingerprint.py
Calcula huella estable de un archivo .replay.
Solo stdlib.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def compute_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str | None:
    if not path.is_file():
        return None
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def build_replay_fingerprint(path: Path) -> dict:
    try:
        stat = path.stat()
        size, mtime = stat.st_size, stat.st_mtime
    except OSError:
        size, mtime = 0, 0.0

    return {
        "path":       str(path),
        "name":       path.name,
        "size_bytes": size,
        "mtime":      mtime,
        "sha256":     compute_sha256(path),
    }