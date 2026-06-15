"""
RLA 2 — parser/extract_metadata_store_dev.py
Extrae metadata de todos los replays parseados y la guarda en SQLite.

Uso:
    python -m rla_app.parser.extract_metadata_store_dev
    python -m rla_app.parser.extract_metadata_store_dev 20
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from rla_app.parser.replay_header_metadata import extract_replay_header_metadata
from rla_app.storage.db_location import get_default_db_path
from rla_app.storage.sqlite_store import ReplayStore


def main() -> None:
    limit: int | None = None
    if len(sys.argv) >= 2:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            limit = None

    db_path = get_default_db_path()
    store   = ReplayStore(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        sql = ("SELECT id, file_path, file_name, parse_json_path, meta_status "
               "FROM processed_replays WHERE parse_json_path IS NOT NULL "
               "ORDER BY id DESC")
        rows = (conn.execute(sql + " LIMIT ?", (limit,)).fetchall()
                if limit else conn.execute(sql).fetchall())
    finally:
        conn.close()

    if not rows:
        print("No hay replays con parse_json_path.")
        sys.exit(0)

    meta_ok = meta_fail = sql_ok = sql_fail = 0

    for row in rows:
        replay_path = Path(row["file_path"])
        json_path   = Path(row["parse_json_path"])
        m = extract_replay_header_metadata(json_path)
        stored = store.update_header_metadata(replay_path, m)

        if stored:
            sql_ok += 1
        else:
            sql_fail += 1

        if m.ok:
            meta_ok += 1
            t0 = m.team0_score if m.team0_score is not None else "?"
            t1 = m.team1_score if m.team1_score is not None else "?"
            secs = f"{m.total_seconds_played:.1f}" if m.total_seconds_played else "—"
            print(f"[OK]   {row['id']} | {row['file_name'][:28]} | "
                  f"{(m.map_name or '—')[:16]} | {(m.match_type or '—')[:9]} | "
                  f"{t0}-{t1} | {secs}s | stored={stored}")
        else:
            meta_fail += 1
            print(f"[FAIL] {row['id']} | {row['file_name'][:28]} | "
                  f"{m.message[:60]} | stored={stored}")

    print(f"\n── Resumen ──────────────────────────────")
    print(f"  DB              : {db_path}")
    print(f"  Filas leídas    : {len(rows)}")
    print(f"  Metadata OK     : {meta_ok}")
    print(f"  Metadata FAIL   : {meta_fail}")
    print(f"  Updates SQL OK  : {sql_ok}")
    print(f"  Updates SQL FAIL: {sql_fail}")

    sys.exit(0 if meta_fail == 0 and sql_fail == 0 else 2)


if __name__ == "__main__":
    main()