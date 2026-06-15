"""
RLA 2 — analysis/session_snapshot.py
Snapshot neutral de la sesión activa más reciente (gap ≤ 2h). Sin W/L.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional

from rla_app.storage.match_reader import RecentMatch, get_recent_matches

_SESSION_GAP = timedelta(hours=2)
_RL_DATE_FMT = "%Y-%m-%d %H-%M-%S"


def _parse_rl_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), _RL_DATE_FMT)
    except ValueError:
        return None


@dataclass(frozen=True)
class SessionSnapshot:
    loaded_matches: int
    total_matches: int
    metadata_ready: int
    metadata_missing: int
    latest_day: Optional[str]
    matches_on_latest_day: int
    online_matches: int
    private_matches: int
    other_match_types: int
    most_played_map: Optional[str]
    most_common_team_size: Optional[int]
    total_seconds: float
    total_minutes_label: str
    average_match_seconds: Optional[float]
    average_match_minutes_label: str
    session_start: Optional[str]
    session_end: Optional[str]
    session_gap_hours: float

    def to_dict(self) -> dict:
        return asdict(self)


def _empty(loaded: int) -> SessionSnapshot:
    return SessionSnapshot(
        loaded_matches=loaded, total_matches=0,
        metadata_ready=0, metadata_missing=0,
        latest_day=None, matches_on_latest_day=0,
        online_matches=0, private_matches=0, other_match_types=0,
        most_played_map=None, most_common_team_size=None,
        total_seconds=0.0, total_minutes_label="0.0",
        average_match_seconds=None, average_match_minutes_label="—",
        session_start=None, session_end=None,
        session_gap_hours=_SESSION_GAP.total_seconds() / 3600,
    )


def build_session_snapshot(limit: int = 50) -> SessionSnapshot:
    all_matches = get_recent_matches(limit)

    # Pares (match, datetime) solo para matches con fecha parseable
    dated: list[tuple[RecentMatch, datetime]] = []
    for m in all_matches:
        dt = _parse_rl_date(m.date)
        if dt is not None:
            dated.append((m, dt))

    if not dated:
        return _empty(len(all_matches))

    # Ordenar por fecha descendente
    dated.sort(key=lambda x: x[1], reverse=True)

    # Construir sesión activa con gap ≤ 2h
    session: list[tuple[RecentMatch, datetime]] = [dated[0]]
    for i in range(1, len(dated)):
        gap = session[-1][1] - dated[i][1]
        if gap <= _SESSION_GAP:
            session.append(dated[i])
        else:
            break

    session_matches = [m for m, _ in session]
    session_dts     = [dt for _, dt in session]

    session_end   = dated[0][0].date
    session_start = session[-1][0].date
    latest_day    = session_dts[0].strftime("%Y-%m-%d")

    matches_on_day = sum(
        1 for _, dt in session if dt.strftime("%Y-%m-%d") == latest_day
    )

    total = len(session_matches)
    meta_ready   = sum(1 for m in session_matches if m.metadata_ready)
    meta_missing = total - meta_ready

    online  = sum(1 for m in session_matches if m.match_type == "Online")
    private = sum(1 for m in session_matches if m.match_type == "Private")
    other   = sum(1 for m in session_matches if m.match_type not in ("Online", "Private"))

    maps  = [m.map_name  for m in session_matches if m.map_name  is not None]
    sizes = [m.team_size for m in session_matches if m.team_size is not None]
    most_map  = Counter(maps).most_common(1)[0][0]  if maps  else None
    most_size = Counter(sizes).most_common(1)[0][0] if sizes else None

    durations  = [m.total_seconds_played for m in session_matches
                  if m.total_seconds_played is not None]
    total_secs = sum(durations)
    avg_secs   = (total_secs / len(durations)) if durations else None

    return SessionSnapshot(
        loaded_matches=len(all_matches),
        total_matches=total,
        metadata_ready=meta_ready,
        metadata_missing=meta_missing,
        latest_day=latest_day,
        matches_on_latest_day=matches_on_day,
        online_matches=online,
        private_matches=private,
        other_match_types=other,
        most_played_map=most_map,
        most_common_team_size=most_size,
        total_seconds=total_secs,
        total_minutes_label=f"{total_secs / 60:.1f}",
        average_match_seconds=avg_secs,
        average_match_minutes_label=f"{avg_secs / 60:.1f}" if avg_secs is not None else "—",
        session_start=session_start,
        session_end=session_end,
        session_gap_hours=_SESSION_GAP.total_seconds() / 3600,
    )