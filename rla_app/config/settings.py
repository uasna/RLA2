"""
RLA 2 — config/settings.py
Configuración runtime de la aplicación.
Sin efectos secundarios al importar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AppSettings:
    """
    Configuración cargada en memoria.
    Los valores se persisten en SQLite (storage layer).
    Este objeto NO hace I/O — es solo un contenedor tipado.
    """
    epic_id: str = ""
    manual_mmr: float = 0.0
    selected_playlist: str = "Ranked Doubles 2v2"
    parser_executable_path: Optional[Path] = None

    # Listas válidas de playlists conocidas
    KNOWN_PLAYLISTS: list[str] = field(default_factory=lambda: [
        "Ranked Duel 1v1",
        "Ranked Doubles 2v2",
        "Ranked Standard 3v3",
        "Unranked",
    ])

    def has_epic_id(self) -> bool:
        return bool(self.epic_id.strip())

    def has_parser(self) -> bool:
        return (
            self.parser_executable_path is not None
            and self.parser_executable_path.exists()
        )
