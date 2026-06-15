"""
RLA 2 — storage/db_location.py
Resuelve la ruta oficial de la base de datos SQLite de RLA 2.
"""
from __future__ import annotations

from pathlib import Path

_DB_NAME = "rla2.db"


def get_default_db_path() -> Path:
    """
    Devuelve la ruta canónica de rla2.db usando el Path Resolver si está disponible.
    Fallback seguro: ~/Documents/My Games/RLA/rla2.db
    """
    try:
        from rla_app.config.paths import RLPathResolver
        paths = RLPathResolver().resolve()
        db_path = paths.app_data_dir / _DB_NAME
    except Exception:
        db_path = Path.home() / "Documents" / "My Games" / "RLA" / _DB_NAME

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path