"""
RLA 2 — storage/register_replay_dev.py
Registra manualmente un .replay existente en SQLite.

Uso:
    python -m rla_app.storage.register_replay_dev "<ruta_replay>"
    python -m rla_app.storage.register_replay_dev "<ruta_replay>" "tmp/rla_dev.db"
"""
from __future__ import annotations

import sys
from pathlib import Path

from rla_app.replay_intake.replay_detector import describe_replay_candidate
from rla_app.storage.db_location import get_default_db_path
from rla_app.storage.sqlite_store import ReplayStore


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m rla_app.storage.register_replay_dev <replay> [db_path]")
        sys.exit(1)

    replay_path = Path(sys.argv[1])
    db_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else get_default_db_path()

    print(f"Replay : {replay_path}")
    print(f"DB     : {db_path}")

    reason = describe_replay_candidate(replay_path)
    if reason != "valid_replay":
        print(f"Resultado: RECHAZADO — {reason}")
        sys.exit(0)

    store = ReplayStore(db_path)

    if store.has_replay(replay_path):
        print("Resultado: Ya estaba registrado.")
        sys.exit(0)

    inserted = store.add_replay(replay_path, status="manual_registered")
    print(f"Resultado: {'Registrado OK.' if inserted else 'No insertado (duplicado).'}")


if __name__ == "__main__":
    main()