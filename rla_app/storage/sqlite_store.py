"""
RLA 2 — storage/sqlite_store.py
Persiste replays, resultados de parseo y metadata de header.
Compatible con DBs existentes (ALTER TABLE seguro).
Solo stdlib + módulos internos.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from rla_app.storage.replay_fingerprint import build_replay_fingerprint

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS processed_replays (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT    NOT NULL UNIQUE,
    file_name       TEXT    NOT NULL,
    size_bytes      INTEGER NOT NULL,
    mtime           REAL    NOT NULL,
    sha256          TEXT,
    status          TEXT    NOT NULL,
    created_at      TEXT    NOT NULL,
    parse_status    TEXT,
    parse_level     TEXT,
    parse_json_path TEXT,
    parse_error_type TEXT,
    parse_message   TEXT,
    parsed_at       TEXT,
    meta_status     TEXT,
    meta_replay_id  TEXT,
    meta_match_guid TEXT,
    meta_replay_name TEXT,
    meta_map_name   TEXT,
    meta_match_type TEXT,
    meta_date       TEXT,
    meta_team_size  INTEGER,
    meta_team0_score INTEGER,
    meta_team1_score INTEGER,
    meta_total_seconds_played REAL,
    meta_num_frames INTEGER,
    meta_record_fps REAL,
    meta_game_version INTEGER,
    meta_build_version TEXT,
    meta_replay_version INTEGER,
    meta_engine_version INTEGER,
    meta_patch_version INTEGER,
    meta_property_count INTEGER,
    meta_message    TEXT,
    metadata_extracted_at TEXT
);
"""

_SHA256_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_processed_replays_sha256
ON processed_replays(sha256) WHERE sha256 IS NOT NULL;
"""

_NEW_COLUMNS: list[tuple[str, str]] = [
    ("sha256",                    "TEXT"),
    ("parse_status",              "TEXT"),
    ("parse_level",               "TEXT"),
    ("parse_json_path",           "TEXT"),
    ("parse_error_type",          "TEXT"),
    ("parse_message",             "TEXT"),
    ("parsed_at",                 "TEXT"),
    ("meta_status",               "TEXT"),
    ("meta_replay_id",            "TEXT"),
    ("meta_match_guid",           "TEXT"),
    ("meta_replay_name",          "TEXT"),
    ("meta_map_name",             "TEXT"),
    ("meta_match_type",           "TEXT"),
    ("meta_date",                 "TEXT"),
    ("meta_team_size",            "INTEGER"),
    ("meta_team0_score",          "INTEGER"),
    ("meta_team1_score",          "INTEGER"),
    ("meta_total_seconds_played", "REAL"),
    ("meta_num_frames",           "INTEGER"),
    ("meta_record_fps",           "REAL"),
    ("meta_game_version",         "INTEGER"),
    ("meta_build_version",        "TEXT"),
    ("meta_replay_version",       "INTEGER"),
    ("meta_engine_version",       "INTEGER"),
    ("meta_patch_version",        "INTEGER"),
    ("meta_property_count",       "INTEGER"),
    ("meta_message",              "TEXT"),
    ("metadata_extracted_at",     "TEXT"),
]


class ReplayStore:
    def __init__(self, db_path: Path) -> None:
        self._db = db_path
        self.initialize()

    def initialize(self) -> None:
        self._db.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)
            self._migrate(conn)
            conn.execute(_SHA256_INDEX)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        existing = {r[1] for r in conn.execute("PRAGMA table_info(processed_replays)")}
        for col, col_type in _NEW_COLUMNS:
            if col not in existing:
                conn.execute(f"ALTER TABLE processed_replays ADD COLUMN {col} {col_type}")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        return conn

    def _resolve(self, path: Path) -> str:
        try:
            return str(path.resolve())
        except OSError:
            return str(path)

    def has_replay(self, path: Path) -> bool:
        key = self._resolve(path)
        fp = build_replay_fingerprint(path)
        sha = fp["sha256"]
        with self._connect() as conn:
            if conn.execute(
                "SELECT 1 FROM processed_replays WHERE file_path = ?", (key,)
            ).fetchone():
                return True
            if sha and conn.execute(
                "SELECT 1 FROM processed_replays WHERE sha256 = ?", (sha,)
            ).fetchone():
                return True
        return False

    def add_replay(self, path: Path, status: str = "detected") -> bool:
        key = self._resolve(path)
        fp = build_replay_fingerprint(path)
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as conn:
                if fp["sha256"] and conn.execute(
                    "SELECT 1 FROM processed_replays WHERE sha256 = ?", (fp["sha256"],)
                ).fetchone():
                    return False
                conn.execute(
                    "INSERT INTO processed_replays "
                    "(file_path, file_name, size_bytes, mtime, sha256, status, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (key, path.name, fp["size_bytes"], fp["mtime"],
                     fp["sha256"], status, now),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def update_parse_result(
        self,
        replay_path: Path,
        ok: bool,
        parse_level: str,
        json_path: Path | None,
        error_type: str | None,
        message: str,
    ) -> bool:
        key = self._resolve(replay_path)
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """UPDATE processed_replays SET
                    parse_status=?, parse_level=?, parse_json_path=?,
                    parse_error_type=?, parse_message=?, parsed_at=?
                WHERE file_path=?""",
                ("ok" if ok else "failed", parse_level,
                 str(json_path) if json_path else None,
                 error_type, message, now, key),
            )
            return cur.rowcount > 0

    def update_header_metadata(self, replay_path: Path, metadata) -> bool:
        key = self._resolve(replay_path)
        now = datetime.now(timezone.utc).isoformat()
        g = lambda attr: getattr(metadata, attr, None)  # noqa: E731
        with self._connect() as conn:
            cur = conn.execute(
                """UPDATE processed_replays SET
                    meta_status=?, meta_replay_id=?, meta_match_guid=?,
                    meta_replay_name=?, meta_map_name=?, meta_match_type=?,
                    meta_date=?, meta_team_size=?, meta_team0_score=?,
                    meta_team1_score=?, meta_total_seconds_played=?,
                    meta_num_frames=?, meta_record_fps=?, meta_game_version=?,
                    meta_build_version=?, meta_replay_version=?,
                    meta_engine_version=?, meta_patch_version=?,
                    meta_property_count=?, meta_message=?,
                    metadata_extracted_at=?
                WHERE file_path=?""",
                (
                    "ok" if g("ok") else "failed",
                    g("replay_id"), g("match_guid"), g("replay_name"),
                    g("map_name"), g("match_type"), g("date"),
                    g("team_size"), g("team0_score"), g("team1_score"),
                    g("total_seconds_played"), g("num_frames"), g("record_fps"),
                    g("game_version"), g("build_version"), g("replay_version"),
                    g("engine_version"), g("patch_version"),
                    g("property_count"), g("message"),
                    now, key,
                ),
            )
            return cur.rowcount > 0

    def get_replay_by_path(self, replay_path: Path) -> dict | None:
        key = self._resolve(replay_path)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM processed_replays WHERE file_path=?", (key,)
            ).fetchone()
        return dict(row) if row else None

    def list_replays(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM processed_replays ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]