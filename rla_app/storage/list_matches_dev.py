"""
RLA 2 — storage/list_matches_dev.py
Lista últimos replays usando columnas meta_* de SQLite. Sin abrir JSON.

Uso:
    python -m rla_app.storage.list_matches_dev
    python -m rla_app.storage.list_matches_dev 10
"""
from __future__ import annotations

import sqlite3
import sys

from rla_app.storage.db_location import get_default_db_path

_SQL = """
SELECT id, file_name, status, parse_status, parse_level,
       meta_status, meta_date, meta_map_name, meta_match_type,
       meta_team_size, meta_team0_score, meta_team1_score,
       meta_total_seconds_played, meta_replay_name
FROM processed_replays
ORDER BY id DESC LIMIT ?
"""


def _s(v, n: int = 0) -> str:
    if v is None:
        return "—"
    s = str(v)
    return (s[:n] + "…") if n and len(s) > n else s


def _row(r) -> str:
    t0    = r["meta_team0_score"] if r["meta_team0_score"] is not None else "?"
    t1    = r["meta_team1_score"] if r["meta_team1_score"] is not None else "?"
    score = f"{t0}-{t1}"
    secs  = (f"{r['meta_total_seconds_played']:.1f}"
             if r["meta_total_seconds_played"] is not None else "—")
    cols = [
        str(r["id"]),
        _s(r["file_name"], 20),
        _s(r["status"], 10),
        _s(r["parse_status"], 7),
        _s(r["meta_status"], 6),
        _s(r["meta_date"], 19),
        _s(r["meta_map_name"], 14),
        _s(r["meta_match_type"], 9),
        _s(r["meta_team_size"]),
        score,
        secs,
        _s(r["meta_replay_name"], 24),
    ]
    return " | ".join(cols)


def main() -> None:
    limit = 20
    if len(sys.argv) >= 2:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            limit = 20

    db_path = get_default_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(_SQL, (limit,)).fetchall()
    finally:
        conn.close()

    if not rows:
        print("No hay replays registrados.")
        return

    header = ("ID | file_name | status | parse | meta | "
              "date | map | type | size | score | secs | replay_name")
    sep = "─" * len(header)
    print(header)
    print(sep)

    meta_ok = meta_missing = 0
    for r in rows:
        print(_row(r))
        if r["meta_status"] == "ok":
            meta_ok += 1
        else:
            meta_missing += 1

    print(f"\n── Resumen ──────────────────────────")
    print(f"  DB           : {db_path}")
    print(f"  Filas leídas : {len(rows)}")
    print(f"  Meta OK      : {meta_ok}")
    print(f"  Meta missing : {meta_missing}")


if __name__ == "__main__":
    main()