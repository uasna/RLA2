"""
RLA 2 — storage/find_orphan_replays_dev.py
Detecta registros en SQLite cuyo file_path ya no existe en disco.

Uso:
    python -m rla_app.storage.find_orphan_replays_dev
    python -m rla_app.storage.find_orphan_replays_dev "tmp/rla_dev.db"
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from rla_app.storage.db_location import get_default_db_path


def main() -> None:
    db_path = Path(sys.argv[1]) if len(sys.argv) >= 2 else get_default_db_path()
    print(f"DB: {db_path}\n")

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, file_path, file_name, status, sha256 "
            "FROM processed_replays ORDER BY id ASC"
        ).fetchall()
    finally:
        conn.close()

    total = len(rows)
    existing = orphans = 0

    for row_id, file_path, file_name, status, sha256 in rows:
        if Path(file_path).is_file():
            existing += 1
        else:
            sha_short = sha256[:10] if sha256 else "NULL"
            print(f"[ORPHAN] {row_id} | {file_name} | {status} | {sha_short}")
            orphans += 1

    print(f"\n── Resumen ──────────────────────")
    print(f"  DB       : {db_path}")
    print(f"  Total    : {total}")
    print(f"  Existentes: {existing}")
    print(f"  Huérfanos : {orphans}")


if __name__ == "__main__":
    main()