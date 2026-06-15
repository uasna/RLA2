"""
RLA 2 — storage/index_replays_folder_dev.py
Indexa todos los .replay de una carpeta en SQLite.

Uso:
    python -m rla_app.storage.index_replays_folder_dev "<carpeta>"
    python -m rla_app.storage.index_replays_folder_dev "<carpeta>" "tmp/rla_dev.db"
"""
from __future__ import annotations

import sys
from pathlib import Path

from rla_app.replay_intake.replay_detector import describe_replay_candidate
from rla_app.storage.db_location import get_default_db_path
from rla_app.storage.sqlite_store import ReplayStore


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m rla_app.storage.index_replays_folder_dev <carpeta> [db_path]")
        sys.exit(1)

    folder = Path(sys.argv[1])
    db_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else get_default_db_path()

    if not folder.is_dir():
        print(f"Error: '{folder}' no existe o no es una carpeta.")
        sys.exit(1)

    print(f"Carpeta : {folder}")
    print(f"DB      : {db_path}\n")

    store = ReplayStore(db_path)

    new = dupes = rejected = 0

    for path in sorted(folder.glob("*.replay")):
        reason = describe_replay_candidate(path)

        if reason != "valid_replay":
            print(f"[BAD: {reason}] {path.name}")
            rejected += 1
            continue

        if store.has_replay(path):
            print(f"[SKIP] {path.name}")
            dupes += 1
            continue

        store.add_replay(path, status="indexed")
        print(f"[NEW]  {path.name}")
        new += 1

    total = new + dupes + rejected
    print(f"\n── Resumen ──────────────────────────")
    print(f"  Encontrados : {total}")
    print(f"  Registrados : {new}")
    print(f"  Duplicados  : {dupes}")
    print(f"  Rechazados  : {rejected}")


if __name__ == "__main__":
    main()