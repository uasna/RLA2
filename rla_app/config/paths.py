"""
RLA 2 — config/paths.py
Path Resolver robusto para Rocket League en Windows.

Detecta automáticamente:
  • Replays con o sin OneDrive  (DemosEpic / Demos)
  • Launch.log con o sin OneDrive
  • Training packs con o sin OneDrive
  • Carpeta de datos internos de RLA

Reglas:
  • Cero rutas hardcodeadas de usuario.
  • Cero imports de UI, watchdog, requests.
  • Usa pathlib + os.environ exclusivamente.
  • Produce un diagnóstico completo en ResolvedRocketLeaguePaths.
  • La carpeta RLA sí se crea automáticamente; las carpetas de RL nunca.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from rla_app.core.errors import AppDataInitError, PathResolutionError
from rla_app.core.models import PathProbe, ResolvedRocketLeaguePaths


# ── Constantes internas ───────────────────────────────────────────────────────

_RL_BASE = Path("My Games", "Rocket League", "TAGame")

# Subcarpetas de replays, en orden de prioridad
_REPLAY_SUBDIRS: list[tuple[str, str]] = [
    ("DemosEpic", "DemosEpic (preferred)"),
    ("Demos",     "Demos (fallback)"),
]

# Prefijos de Documents, en orden de prioridad
_DOCS_PREFIXES: list[tuple[str, str]] = [
    ("OneDrive",  "OneDrive\\Documents"),
    ("",          "Documents"),
]

_RLA_DIR_NAME = Path("My Games", "RLA")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_profile() -> Path:
    """
    Devuelve USERPROFILE de forma segura.
    En Linux/macOS (tests) usa HOME como fallback.
    """
    raw = os.environ.get("USERPROFILE") or os.environ.get("HOME", "")
    if not raw:
        raise PathResolutionError(
            "No se encontró USERPROFILE ni HOME en las variables de entorno."
        )
    return Path(raw)


def _resolve_documents_root(userprofile: Path) -> list[tuple[Path, str]]:
    """
    Devuelve lista de rutas candidatas para la carpeta Documents
    (OneDrive primero, luego Documents local).
    """
    candidates: list[tuple[Path, str]] = []

    # OneDrive puede estar en varias ubicaciones
    # Primero intentamos con la variable de entorno si existe
    onedrive_env = os.environ.get("OneDrive") or os.environ.get("ONEDRIVE")
    if onedrive_env:
        od = Path(onedrive_env)
        docs_via_env = od / "Documents"
        candidates.append((docs_via_env, f"OneDrive[env]\\Documents ({docs_via_env})"))

    # Luego intentamos las rutas convencionales
    for prefix, label in _DOCS_PREFIXES:
        if prefix:
            docs = userprofile / prefix / "Documents"
        else:
            docs = userprofile / "Documents"
        candidates.append((docs, label))

    return candidates


def _probe_path(path: Path, label: str) -> PathProbe:
    return PathProbe(path=path, exists=path.exists(), label=label)


# ── Candidatos de replays ─────────────────────────────────────────────────────

def _build_replay_candidates(userprofile: Path) -> list[tuple[Path, str]]:
    """
    Genera lista ordenada de rutas candidatas para la carpeta de replays.
    Orden: OneDrive/DemosEpic, OneDrive/Demos, Docs/DemosEpic, Docs/Demos
    """
    candidates: list[tuple[Path, str]] = []
    docs_roots = _resolve_documents_root(userprofile)

    for docs_path, docs_label in docs_roots:
        for subdir, subdir_label in _REPLAY_SUBDIRS:
            full = docs_path / _RL_BASE / subdir
            label = f"{docs_label} → {subdir_label}"
            candidates.append((full, label))

    return candidates


def _build_log_candidates(userprofile: Path) -> list[tuple[Path, str]]:
    """Genera candidatos para Launch.log."""
    candidates: list[tuple[Path, str]] = []
    docs_roots = _resolve_documents_root(userprofile)
    for docs_path, docs_label in docs_roots:
        full = docs_path / _RL_BASE / "Logs" / "Launch.log"
        candidates.append((full, f"{docs_label} → Logs/Launch.log"))
    return candidates


def _build_training_candidates(userprofile: Path) -> list[tuple[Path, str]]:
    """
    Genera candidatos para la carpeta de training packs.
    El segmento '0000000000000000' es un placeholder conocido de RL.
    """
    candidates: list[tuple[Path, str]] = []
    docs_roots = _resolve_documents_root(userprofile)
    for docs_path, docs_label in docs_roots:
        full = docs_path / _RL_BASE / "Training" / "0000000000000000" / "MyTraining"
        candidates.append((full, f"{docs_label} → Training/MyTraining"))
    return candidates


# ── Inicialización de la carpeta RLA ──────────────────────────────────────────

def _init_app_data(userprofile: Path) -> Path:
    """
    Crea la estructura de datos interna de RLA si no existe.
    Esta carpeta sí puede crearse automáticamente.
    Levanta AppDataInitError si no es posible.
    """
    base = userprofile / "Documents" / _RLA_DIR_NAME

    subdirs = [
        base / "logs",
        base / "replay_json",
        base / "cache",
        base / "training_template_bank",
    ]

    try:
        base.mkdir(parents=True, exist_ok=True)
        for sub in subdirs:
            sub.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise AppDataInitError(
            f"No se pudo crear la carpeta de datos de RLA en '{base}': {exc}"
        ) from exc

    return base


# ── Path Resolver principal ───────────────────────────────────────────────────

class RLPathResolver:
    """
    Resuelve todas las rutas relevantes para RLA 2.

    Uso:
        resolver = RLPathResolver()
        paths = resolver.resolve()
        for line in paths.summary_lines():
            print(line)
    """

    def resolve(self) -> ResolvedRocketLeaguePaths:
        userprofile = _user_profile()
        warnings: list[str] = []
        errors: list[str] = []

        # ── Replays ───────────────────────────────────────────────────────────
        replay_candidates = _build_replay_candidates(userprofile)
        probed_replays: list[PathProbe] = []
        resolved_replays: Optional[Path] = None

        for path, label in replay_candidates:
            probe = _probe_path(path, label)
            probed_replays.append(probe)
            if probe.exists and resolved_replays is None:
                resolved_replays = path

        if resolved_replays is None:
            errors.append(
                "No se encontró ninguna carpeta de replays válida. "
                "Verifica que Rocket League haya sido ejecutado al menos una vez."
            )

        # ── Logs ─────────────────────────────────────────────────────────────
        log_candidates = _build_log_candidates(userprofile)
        probed_logs: list[PathProbe] = []
        resolved_log: Optional[Path] = None

        for path, label in log_candidates:
            probe = _probe_path(path, label)
            probed_logs.append(probe)
            if probe.exists and resolved_log is None:
                resolved_log = path

        if resolved_log is None:
            warnings.append(
                "No se encontró Launch.log. Algunas funciones de log de partida "
                "no estarán disponibles."
            )

        # ── Training ──────────────────────────────────────────────────────────
        training_candidates = _build_training_candidates(userprofile)
        probed_training: list[PathProbe] = []
        resolved_training: Optional[Path] = None

        for path, label in training_candidates:
            probe = _probe_path(path, label)
            probed_training.append(probe)
            if probe.exists and resolved_training is None:
                resolved_training = path

        if resolved_training is None:
            warnings.append(
                "No se encontró la carpeta MyTraining. "
                "Las funciones de training pack no estarán disponibles "
                "hasta que exista la carpeta en disco."
            )

        # ── App Data ──────────────────────────────────────────────────────────
        try:
            app_data = _init_app_data(userprofile)
        except AppDataInitError as exc:
            errors.append(str(exc))
            # Ruta de emergencia en temp — nunca debe usarse en producción
            import tempfile
            app_data = Path(tempfile.gettempdir()) / "RLA_EMERGENCY"
            app_data.mkdir(parents=True, exist_ok=True)

        return ResolvedRocketLeaguePaths(
            replays_dir=resolved_replays,
            logs_file=resolved_log,
            training_dir=resolved_training,
            app_data_dir=app_data,
            app_db_path=app_data / "app.db",
            app_logs_dir=app_data / "logs",
            app_replay_json_dir=app_data / "replay_json",
            app_cache_dir=app_data / "cache",
            app_training_bank_dir=app_data / "training_template_bank",
            probed_replays=probed_replays,
            probed_logs=probed_logs,
            probed_training=probed_training,
            warnings=warnings,
            errors=errors,
        )


# ── Instancia singleton reutilizable ──────────────────────────────────────────

_default_resolver: Optional[RLPathResolver] = None


def get_default_resolver() -> RLPathResolver:
    global _default_resolver
    if _default_resolver is None:
        _default_resolver = RLPathResolver()
    return _default_resolver
