"""
RLA 2 — replay_intake/replay_detector.py
Decide si un archivo es un candidato válido de replay.
Solo stdlib. Sin dependencias externas.
"""
from __future__ import annotations

from pathlib import Path

_TEMP_SUFFIXES = {".tmp", ".part", ".crdownload", ".download"}


def describe_replay_candidate(path: Path) -> str:
    if path.name.startswith("~"):
        return "temporary_file"
    if path.suffix.lower() in _TEMP_SUFFIXES:
        return "temporary_file"
    if not path.exists():
        return "not_found"
    if not path.is_file():
        return "not_file"
    if path.suffix.lower() != ".replay":
        return "wrong_extension"
    try:
        if path.stat().st_size == 0:
            return "empty_file"
    except OSError:
        return "os_error"
    return "valid_replay"


def is_replay_candidate(path: Path) -> bool:
    return describe_replay_candidate(path) == "valid_replay"