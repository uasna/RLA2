"""
RLA 2 — parser/list_metadata_dev.py
Lista metadata de últimos replays desde SQLite.

Uso:
    python -m rla_app.parser.list_metadata_dev
    python -m rla_app.parser.list_metadata_dev 10
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from rla_app.parser.replay_header_metadata import extract_replay_header_metadata
from rla_app.storage.db_location import get_default_db_path


def _short(s: str | None, n: int = 28) -> str:
    if not s:
        return "—"
    return s[:n] + "…" if len(s) > n else s


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
        rows = conn.execute(
            "SELECT id, file_name, parse_json_path, parse_status, parse_level "
            "FROM processed_replays "
            "WHERE parse_json_path IS NOT NULL "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        print("No hay replays con parse_json_path en la DB.")
        return

    meta_ok = meta_fail = 0

    header = (f"{'ID':<5} {'file_name':<26} {'lvl':<12} {'ok':<5} "
              f"{'date':<22} {'map':<16} {'type':<10} "
              f"{'sz':<3} {'score':<6} {'secs':<7} replay_name")
    print(header)
    print("─" * 130)

    for row in rows:
        m = extract_replay_header_metadata(Path(row["parse_json_path"]))
        if m.ok:
            meta_ok += 1
            score = f"{m.team0_score}-{m.team1_score if m.team1_score is not None else '?'}"
            secs  = f"{m.total_seconds_played:.1f}" if m.total_seconds_played else "—"
            print(
                f"{row['id']:<5} {_short(row['file_name']):<26} "
                f"{(row['parse_level'] or '—'):<12} {'✓':<5} "
                f"{_short(m.date, 21):<22} {_short(m.map_name, 15):<16} "
                f"{_short(m.match_type, 9):<10} "
                f"{str(m.team_size or '—'):<3} {score:<6} {secs:<7} "
                f"{_short(m.replay_name, 24)}"
            )
        else:
            meta_fail += 1
            print(f"{row['id']:<5} {_short(row['file_name']):<26} "
                  f"{(row['parse_level'] or '—'):<12} {'✗':<5} "
                  f"[{_short(m.message, 60)}]")

    print(f"\n── Resumen ──────────────────────────")
    print(f"  DB           : {db_path}")
    print(f"  Filas leídas : {len(rows)}")
    print(f"  Metadata OK  : {meta_ok}")
    print(f"  Metadata FAIL: {meta_fail}")


if __name__ == "__main__":
    main()