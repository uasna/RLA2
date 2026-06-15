"""
RLA 2 — storage/match_reader.py
Capa limpia de lectura para la UI. Sin prints. Sin side-effects.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from rla_app.storage.db_location import get_default_db_path

_SQL = """
SELECT id, file_name, status, parse_status, parse_level,
       meta_status, meta_date, meta_map_name, meta_match_type,
       meta_team_size, meta_team0_score, meta_team1_score,
       meta_total_seconds_played, meta_replay_name
FROM processed_replays
ORDER BY id DESC LIMIT ?
"""


@dataclass(frozen=True)
class RecentMatch:
    id: int
    file_name: str
    status: Optional[str]
    parse_status: Optional[str]
    parse_level: Optional[str]
    meta_status: Optional[str]
    date: Optional[str]
    map_name: Optional[str]
    match_type: Optional[str]
    team_size: Optional[int]
    team0_score: Optional[int]
    team1_score: Optional[int]
    total_seconds_played: Optional[float]
    replay_name: Optional[str]
    score_label: str
    seconds_label: str
    metadata_ready: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _build(row: sqlite3.Row) -> RecentMatch:
    t0 = row["meta_team0_score"]
    t1 = row["meta_team1_score"]
    secs = row["meta_total_seconds_played"]
    return RecentMatch(
        id=row["id"],
        file_name=row["file_name"] or "",
        status=row["status"],
        parse_status=row["parse_status"],
        parse_level=row["parse_level"],
        meta_status=row["meta_status"],
        date=row["meta_date"],
        map_name=row["meta_map_name"],
        match_type=row["meta_match_type"],
        team_size=row["meta_team_size"],
        team0_score=t0,
        team1_score=t1,
        total_seconds_played=secs,
        replay_name=row["meta_replay_name"],
        score_label=f"{t0 if t0 is not None else '?'}-{t1 if t1 is not None else '?'}",
        seconds_label=f"{secs:.1f}" if secs is not None else "—",
        metadata_ready=row["meta_status"] == "ok",
    )


def get_recent_matches(
    limit: int = 20,
    db_path: Path | None = None,
) -> list[RecentMatch]:
    path = db_path or get_default_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(_SQL, (limit,)).fetchall()
    finally:
        conn.close()
    return [_build(r) for r in rows]