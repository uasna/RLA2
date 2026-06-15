"""
RLA 2 — storage/backfill_sha256_dev.py
Rellena sha256 en registros antiguos donde sha256 IS NULL.

Uso:
    python -m rla_app.storage.backfill_sha256_dev
    python -m rla_app.storage.backfill_sha256_dev "tmp/rla_dev.db"
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from rla_app.storage.db_location import get_default_db_path
from rla_app.storage.replay_fingerprint import compute_sha256


def main() -> None:
    db_path = Path(sys.argv[1]) if len(sys.argv) >= 2 else get_default_db_path()
    print(f"DB: {db_path}\n")

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, file_path, file_name FROM processed_replays "
            "WHERE sha256 IS NULL ORDER BY id ASC"
        ).fetchall()

        print(f"Pendientes: {len(rows)}\n")
        updated = missing = dupes = 0

        for row_id, file_path, file_name in rows:
            sha = compute_sha256(Path(file_path))

            if sha is None:
                print(f"[MISS]     {row_id} {file_name}")
                missing += 1
                continue

            try:
                conn.execute(
                    "UPDATE processed_replays SET sha256 = ? WHERE id = ?",
                    (sha, row_id),
                )
                conn.commit()
                print(f"[OK]       {row_id} {file_name}")
                updated += 1
            except sqlite3.IntegrityError:
                print(f"[DUP-HASH] {row_id} {file_name}")
                dupes += 1

    finally:
        conn.close()

    print(f"\n── Resumen ──────────────────────")
    print(f"  Actualizados          : {updated}")
    print(f"  Faltantes/fallidos    : {missing}")
    print(f"  Duplicados por hash   : {dupes}")


if __name__ == "__main__":
    main()