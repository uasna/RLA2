"""
RLA 2 — storage/list_replays_dev.py
Lista los últimos replays registrados en SQLite.

Uso:
    python -m rla_app.storage.list_replays_dev
    python -m rla_app.storage.list_replays_dev "tmp/rla_dev.db" 10
"""
from __future__ import annotations

import sys
from pathlib import Path

from rla_app.storage.db_location import get_default_db_path
from rla_app.storage.sqlite_store import ReplayStore


def main() -> None:
    db_path = Path(sys.argv[1]) if len(sys.argv) >= 2 else get_default_db_path()

    limit = 20
    if len(sys.argv) >= 3:
        try:
            limit = int(sys.argv[2])
        except ValueError:
            limit = 20

    store = ReplayStore(db_path)
    rows = store.list_replays(limit)

    print(f"DB       : {db_path}")
    print(f"Mostrando: {len(rows)} replay(s)\n")

    if not rows:
        print("No hay replays registrados.")
        return

    print(f"{'ID':<5} {'file_name':<40} {'status':<18} {'size_bytes':<12} {'sha256':<12} created_at")
    print("-" * 110)
    for r in rows:
        sha_short = (r["sha256"][:10] if r.get("sha256") else "NULL")
        print(
            f"{r['id']:<5} {r['file_name']:<40} {r['status']:<18} "
            f"{r['size_bytes']:<12} {sha_short:<12} {r['created_at']}"
        )


if __name__ == "__main__":
    main()