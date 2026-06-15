"""
RLA 2 — replay_intake/watcher.py
Vigila carpeta de replays con watchdog.
"""
from __future__ import annotations

import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from rla_app.replay_intake.replay_event_handler import handle_replay_file

_DEBOUNCE_SECONDS = 2.0


def _publish(bus, category: str, message: str, payload: dict | None = None) -> None:
    payload = payload or {}
    for method_name in ("publish", "emit"):
        method = getattr(bus, method_name, None)
        if method is None:
            continue
        for call in (
            lambda m=method: m(category=category, message=message, payload=payload),
            lambda m=method: m(category, message, payload),
            lambda m=method: m(category, message),
        ):
            try:
                call()
                return
            except TypeError:
                continue


class _ReplayHandler(FileSystemEventHandler):
    def __init__(self, event_bus, replay_store=None) -> None:
        super().__init__()
        self._bus = event_bus
        self._store = replay_store
        self._lock = threading.Lock()
        self._last_seen: dict[str, float] = {}

    def _debounced(self, src: str) -> bool:
        now = time.monotonic()
        with self._lock:
            if now - self._last_seen.get(src, 0.0) < _DEBOUNCE_SECONDS:
                return False
            self._last_seen[src] = now
        return True

    def _dispatch(self, src_path: str) -> None:
        path = Path(src_path)
        if path.is_dir():
            return
        if not self._debounced(src_path):
            return
        threading.Thread(
            target=handle_replay_file,
            args=(path, self._bus),
            kwargs={"replay_store": self._store},
            daemon=True,
        ).start()

    def on_created(self, event) -> None:
        if not event.is_directory:
            self._dispatch(event.src_path)

    def on_moved(self, event) -> None:
        if not event.is_directory:
            self._dispatch(event.dest_path)


class ReplayFolderWatcher:
    def __init__(
        self,
        replays_dir: Path,
        event_bus,
        replay_store=None,
        recursive: bool = False,
    ) -> None:
        self._dir = replays_dir
        self._bus = event_bus
        self._store = replay_store
        self._recursive = recursive
        self._observer: Observer | None = None

    def start(self) -> None:
        if not self._dir.is_dir():
            _publish(self._bus, "WATCHER_ERROR",
                     f"Carpeta no encontrada: {self._dir}")
            return
        self._observer = Observer()
        self._observer.schedule(
            _ReplayHandler(self._bus, self._store),
            str(self._dir),
            recursive=self._recursive,
        )
        self._observer.start()
        _publish(self._bus, "WATCHER_STARTED", f"Vigilando: {self._dir}")

    def stop(self) -> None:
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join()
        self._observer = None
        _publish(self._bus, "WATCHER_STOPPED", "Watcher detenido")

    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()