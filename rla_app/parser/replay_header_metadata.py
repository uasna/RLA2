"""
RLA 2 — parser/replay_header_metadata.py
Extrae metadata básica desde un JSON header-only de Rattletrap.
Solo stdlib. Sin prints. Sin SQLite.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ReplayHeaderMetadata:
    ok: bool
    json_path: Path
    replay_id: str | None = None
    match_guid: str | None = None
    replay_name: str | None = None
    map_name: str | None = None
    match_type: str | None = None
    date: str | None = None
    team_size: int | None = None
    team0_score: int | None = None
    team1_score: int | None = None
    total_seconds_played: float | None = None
    num_frames: int | None = None
    record_fps: float | None = None
    game_version: int | None = None
    build_version: str | None = None
    replay_version: int | None = None
    engine_version: int | None = None
    patch_version: int | None = None
    property_count: int = 0
    message: str = ""


# ── Helpers de tipo ───────────────────────────────────────────────────────────

def _as_int(v: Any) -> int | None:
    try:
        return int(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _as_float(v: Any) -> float | None:
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _as_str(v: Any) -> str | None:
    return str(v) if v is not None else None


# ── Acceso seguro al JSON ─────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_header_properties(data: dict) -> list:
    try:
        elements = data["header"]["body"]["properties"]["elements"]
        return elements if isinstance(elements, list) else []
    except (KeyError, TypeError):
        return []


def properties_to_dict(elements: list) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for el in elements:
        if isinstance(el, list) and len(el) == 2 and isinstance(el[0], str):
            out[el[0]] = el[1]
    return out


def extract_property_value(payload: dict) -> Any:
    if not isinstance(payload, dict):
        return None
    value = payload.get("value")
    if not isinstance(value, dict):
        return None
    for key in ("int", "float", "str", "name", "q_word", "bool", "byte", "word"):
        if key in value:
            return value[key]
    return None


# ── Extractor principal ───────────────────────────────────────────────────────

def extract_replay_header_metadata(json_path: Path) -> ReplayHeaderMetadata:
    if not json_path.is_file():
        return ReplayHeaderMetadata(ok=False, json_path=json_path,
                                    message=f"Archivo no encontrado: {json_path}")
    try:
        data = load_json(json_path)
    except Exception as exc:
        return ReplayHeaderMetadata(ok=False, json_path=json_path,
                                    message=f"Error cargando JSON: {exc}")

    elements = get_header_properties(data)
    if not elements:
        return ReplayHeaderMetadata(ok=False, json_path=json_path,
                                    message="No se encontró header.body.properties.elements")

    props = properties_to_dict(elements)
    get = lambda name: extract_property_value(props[name]) if name in props else None  # noqa: E731

    # engine/patch version desde header.body directamente
    header_body = data.get("header", {}).get("body", {})

    return ReplayHeaderMetadata(
        ok=True,
        json_path=json_path,
        replay_id=_as_str(get("Id")),
        match_guid=_as_str(get("MatchGUID")),
        replay_name=_as_str(get("ReplayName")),
        map_name=_as_str(get("MapName")),
        match_type=_as_str(get("MatchType")),
        date=_as_str(get("Date")),
        team_size=_as_int(get("TeamSize")),
        team0_score=_as_int(get("Team0Score")),
        team1_score=_as_int(get("Team1Score")),
        total_seconds_played=_as_float(get("TotalSecondsPlayed")),
        num_frames=_as_int(get("NumFrames")),
        record_fps=_as_float(get("RecordFPS")),
        game_version=_as_int(get("GameVersion")),
        build_version=_as_str(get("BuildVersion")),
        replay_version=_as_int(get("ReplayVersion")),
        engine_version=_as_int(header_body.get("engine_version")),
        patch_version=_as_int(header_body.get("patch_version")),
        property_count=len(elements),
        message="OK",
    )