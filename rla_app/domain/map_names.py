"""
RLA 2 — domain/map_names.py
Normaliza nombres internos de mapas de Rocket League para la UI.
Solo stdlib. Sin red. Sin SQLite. Sin prints.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MapNameInfo:
    raw: str | None
    display_name: str
    short_name: str
    family: str | None
    variant: str | None
    source: str


# Solo mapas con nombre oficial confirmado
_KNOWN_MAPS: dict[str, tuple[str, str, str | None, str | None]] = {
    "NeoTokyo_Standard_P": ("Neo Tokyo", "Neo Tokyo", "Neo Tokyo", "Standard"),
}

# Acrónimos conocidos (lowercase key → display form)
_ACRONYMS: dict[str, str] = {
    "uf":  "UF",
    "ff":  "FF",
    "cs":  "CS",
    "grs": "GRS",
}

_SUFFIX_RE = re.compile(r"_[Pp]$")


def _normalize_token(token: str) -> str:
    """Aplica acrónimo si corresponde, sino Title-case básico."""
    lower = token.lower()
    if lower in _ACRONYMS:
        return _ACRONYMS[lower]
    # Preservar tokens que empiezan con dígito (ej. 10A)
    if token and token[0].isdigit():
        return token.upper()
    return token[:1].upper() + token[1:].lower() if token else token


def _fallback(raw: str) -> MapNameInfo:
    # Quitar sufijo _P / _p de forma case-insensitive
    cleaned = _SUFFIX_RE.sub("", raw)

    # Reemplazar _ por espacio
    cleaned = cleaned.replace("_", " ")

    # Separar CamelCase básico (myMap → my Map)
    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", cleaned)

    # Limpiar espacios dobles
    cleaned = re.sub(r" {2,}", " ", cleaned).strip()

    # Tokenizar y normalizar cada token
    tokens  = cleaned.split(" ") if cleaned else []
    display = " ".join(_normalize_token(t) for t in tokens if t) or raw

    parts   = display.split(" ", 1)
    family  = parts[0] if parts else None
    variant = parts[1] if len(parts) > 1 else None

    return MapNameInfo(
        raw=raw, display_name=display, short_name=display,
        family=family, variant=variant, source="fallback",
    )


def normalize_map_name(raw: str | None) -> MapNameInfo:
    if not raw or not raw.strip():
        return MapNameInfo(
            raw=raw, display_name="Unknown Map", short_name="Unknown",
            family=None, variant=None, source="missing",
        )

    known = _KNOWN_MAPS.get(raw)
    if known:
        display, short, family, variant = known
        return MapNameInfo(
            raw=raw, display_name=display, short_name=short,
            family=family, variant=variant, source="known",
        )

    return _fallback(raw)


def get_display_map_name(raw: str | None) -> str:
    return normalize_map_name(raw).display_name