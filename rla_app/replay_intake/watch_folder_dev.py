"""
RLA 2 — replay_intake/watch_folder_dev.py
Dev runner para probar watcher + SQLite desde terminal.

Uso:
    python -m rla_app.replay_intake.watch_folder_dev "<ruta_replays>"
    python -m rla_app.replay_intake.watch_folder_dev "<ruta_replays>" "tmp/rla_dev.db"
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from rla_app.replay_intake.watcher import ReplayFolderWatcher
from rla_app.storage.db_location import get_default_db_path
from rla_app.storage.sqlite_store import ReplayStore


class PrintBus:
    def publish(self, category, message, payload=None) -> None:
        print(f"[{category}] {message}")
        if payload:
            print(f"  payload: {payload}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m rla_app.replay_intake.watch_folder_dev <ruta> [db_path]")
        sys.exit(1)

    folder = Path(sys.argv[1])
    db_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else get_default_db_path()

    print(f"Carpeta vigilada : {folder}")
    print(f"Base de datos    : {db_path}")

    bus = PrintBus()
    store = ReplayStore(db_path)
    watcher = ReplayFolderWatcher(folder, bus, replay_store=store)
    watcher.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
        print("Watcher detenido.")


if __name__ == "__main__":
    main()