"""
RLA 2 — core/models.py
Modelos puros de dominio.
Sin imports de UI, watchdog, requests ni ninguna lib externa.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Optional


# ── Enumeraciones ─────────────────────────────────────────────────────────────

class AppEventLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AppEventCategory(Enum):
    PATHS = "PATHS"
    WATCHER = "WATCHER"
    REPLAY = "REPLAY"
    MMR = "MMR"
    PARSER = "PARSER"
    TRAINING = "TRAINING"
    STORAGE = "STORAGE"
    SYSTEM = "SYSTEM"


class ReplayProcessingStatus(Enum):
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    DUPLICATE = auto()


class ParserStatus(Enum):
    NOT_CONFIGURED = auto()
    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()


class MmrStatus(Enum):
    SUCCESS = auto()
    FALLBACK_MANUAL = auto()
    NOT_CONFIGURED = auto()
    FAILED = auto()


class PathResolutionStatus(Enum):
    FOUND = auto()
    NOT_FOUND = auto()
    FALLBACK_USED = auto()


# ── Path Resolution ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PathProbe:
    """Resultado de verificar una ruta candidata individual."""
    path: Path
    exists: bool
    label: str  # descripción humana, p.ej. "OneDrive DemosEpic"


@dataclass
class ResolvedRocketLeaguePaths:
    """
    Resultado canónico del proceso de resolución de rutas.
    Todas las rutas son Optional porque pueden no existir.
    """
    replays_dir: Optional[Path]
    logs_file: Optional[Path]
    training_dir: Optional[Path]
    app_data_dir: Path               # siempre presente, creada por RLA
    app_db_path: Path
    app_logs_dir: Path
    app_replay_json_dir: Path
    app_cache_dir: Path
    app_training_bank_dir: Path

    # Diagnóstico
    probed_replays: list[PathProbe] = field(default_factory=list)
    probed_logs: list[PathProbe] = field(default_factory=list)
    probed_training: list[PathProbe] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def replays_ok(self) -> bool:
        return self.replays_dir is not None and self.replays_dir.exists()

    @property
    def logs_ok(self) -> bool:
        return self.logs_file is not None and self.logs_file.exists()

    @property
    def training_ok(self) -> bool:
        return self.training_dir is not None and self.training_dir.exists()

    def summary_lines(self) -> list[str]:
        """Genera líneas de diagnóstico legibles para el log de UI."""
        lines: list[str] = []
        lines.append("── PATH RESOLUTION REPORT ──────────────────────────")
        lines.append(f"  Replays  : {'✓ ' + str(self.replays_dir) if self.replays_ok else '✗ NOT FOUND'}")
        lines.append(f"  Log file : {'✓ ' + str(self.logs_file) if self.logs_ok else '✗ NOT FOUND'}")
        lines.append(f"  Training : {'✓ ' + str(self.training_dir) if self.training_ok else '✗ NOT FOUND'}")
        lines.append(f"  App data : ✓ {self.app_data_dir}")
        if self.warnings:
            lines.append("  Warnings:")
            for w in self.warnings:
                lines.append(f"    ⚠ {w}")
        if self.errors:
            lines.append("  Errors:")
            for e in self.errors:
                lines.append(f"    ✗ {e}")
        lines.append("────────────────────────────────────────────────────")
        return lines


# ── App Events ────────────────────────────────────────────────────────────────

@dataclass
class AppEvent:
    """Evento interno del sistema, enrutado por el Event Bus."""
    level: AppEventLevel
    category: AppEventCategory
    message: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    payload: dict = field(default_factory=dict)

    def __str__(self) -> str:
        ts = self.created_at.strftime("%H:%M:%S")
        return f"[{ts}] [{self.level.value}] [{self.category.value}] {self.message}"


# ── Replay ────────────────────────────────────────────────────────────────────

@dataclass
class ReplayFile:
    """Metadatos de un archivo .replay detectado en disco."""
    path: Path
    sha256: str
    size_bytes: int
    detected_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def name(self) -> str:
        return self.path.name


@dataclass
class ReplayProcessingJob:
    """Trabajo de procesamiento asociado a un replay detectado."""
    replay: ReplayFile
    status: ReplayProcessingStatus = ReplayProcessingStatus.PENDING
    parser_status: ParserStatus = ParserStatus.SKIPPED
    mmr_status: MmrStatus = MmrStatus.NOT_CONFIGURED
    json_output_path: Optional[Path] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# ── MMR ──────────────────────────────────────────────────────────────────────

@dataclass
class MmrSnapshot:
    """Instantánea de MMR asociada a un replay o momento concreto."""
    epic_id: str
    playlist: str
    mmr: float
    rank: str
    division: str
    source: str          # "network" | "manual" | "stub"
    replay_sha256: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


# ── Parser ───────────────────────────────────────────────────────────────────

@dataclass
class ReplayParseResult:
    """Resultado de parsear un .replay a JSON y extraer telemetría básica."""
    replay_sha256: str
    json_path: Optional[Path]
    goals: int = 0
    assists: int = 0
    shots: int = 0
    saves: int = 0
    players: list[str] = field(default_factory=list)
    blue_score: int = 0
    orange_score: int = 0
    # Placeholders para telemetría avanzada futura
    shot_speed_placeholder: None = None
    touches_placeholder: None = None
    boost_placeholder: None = None


# ── Training Packs ────────────────────────────────────────────────────────────

@dataclass
class TrainingPackInstallPlan:
    """Plan de instalación de un training pack (siempre validado antes de ejecutar)."""
    source_tem: Path
    destination_dir: Path
    pack_name: str
    sha256_expected: str
    size_bytes_expected: int
    dry_run: bool = True            # por defecto, nunca ejecutar sin confirmación
    backup_path: Optional[Path] = None
