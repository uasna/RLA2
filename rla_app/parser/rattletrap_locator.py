"""
RLA 2 — parser/rattletrap_locator.py
Localiza el binario Rattletrap y prepara la carpeta de salida JSON.
Solo stdlib. Sin subprocess. Sin parseo.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RattletrapInfo:
    found: bool
    path: Path | None
    source: str
    message: str


def find_rattletrap(project_root: Path | None = None) -> RattletrapInfo:
    # a) Variable de entorno
    env_val = os.environ.get("RLA_RATTLETRAP_PATH")
    if env_val:
        p = Path(env_val)
        if p.is_file():
            return RattletrapInfo(True, p, "env:RLA_RATTLETRAP_PATH", f"Encontrado via env: {p}")
        return RattletrapInfo(False, None, "env:RLA_RATTLETRAP_PATH",
                              f"RLA_RATTLETRAP_PATH apunta a ruta inválida: {p}")

    # b) Carpeta local tools/
    root = project_root or Path(__file__).parent.parent.parent
    local = root / "tools" / "rattletrap" / "rattletrap.exe"
    if local.is_file():
        return RattletrapInfo(True, local, "local:tools/rattletrap", f"Encontrado local: {local}")

    # c/d) PATH del sistema
    for name in ("rattletrap", "rattletrap.exe"):
        which = shutil.which(name)
        if which:
            p = Path(which)
            return RattletrapInfo(True, p, f"system:PATH({name})", f"Encontrado en PATH: {p}")

    return RattletrapInfo(
        found=False,
        path=None,
        source="not_found",
        message=(
            "Rattletrap no encontrado. Opciones: "
            "(1) set RLA_RATTLETRAP_PATH=<ruta>, "
            "(2) colocar en tools/rattletrap/rattletrap.exe, "
            "(3) agregar al PATH del sistema."
        ),
    )


def get_parser_output_dir() -> Path:
    try:
        from rla_app.config.paths import RLPathResolver
        base = RLPathResolver().resolve().app_data_dir
    except Exception:
        base = Path.home() / "Documents" / "My Games" / "RLA"

    out = base / "parsed_replays"
    out.mkdir(parents=True, exist_ok=True)
    return out