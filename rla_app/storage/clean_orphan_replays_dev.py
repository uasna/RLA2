"""
RLA 2 — storage/clean_orphan_replays_dev.py
Elimina de SQLite registros cuyo file_path ya no existe en disco.
Requiere confirmación explícita antes de borrar.

Uso:
    python -m rla_app.storage.clean_orphan_replays_dev
    python -m rla_app.storage.clean_orphan_replays_dev "tmp/rla_dev.db"
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

        total = len(rows)
        orphans: list[tuple] = []

        for row in rows:
            row_id, file_path, file_name, status, sha256 = row
            if not Path(file_path).is_file():
                sha_short = sha256[:10] if sha256 else "NULL"
                print(f"[ORPHAN] {row_id} | {file_name} | {status} | {sha_short}")
                orphans.append(row)

        if not orphans:
            print("No hay registros huérfanos.")
            return

        print(f"\n{len(orphans)} huérfano(s) detectado(s).")
        confirm = input("\nEscribe DELETE para eliminar estos registros huérfanos: ").strip()

        deleted = 0
        if confirm == "DELETE":
            for row in orphans:
                conn.execute("DELETE FROM processed_replays WHERE id = ?", (row[0],))
                deleted += 1
            conn.commit()
        else:
            print("Cancelado.")

    finally:
        conn.close()

    print(f"\n── Resumen ──────────────────────")
    print(f"  DB                 : {db_path}")
    print(f"  Total revisados    : {total}")
    print(f"  Huérfanos detectados: {len(orphans)}")
    print(f"  Eliminados         : {deleted}")


if __name__ == "__main__":
    main()