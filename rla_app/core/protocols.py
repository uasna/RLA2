"""
RLA 2 — core/protocols.py
Interfaces (Protocols) que permiten invertir dependencias.
Los módulos concretos dependen de estas abstracciones, no al revés.
Sin dependencias externas.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

from rla_app.core.models import (
    AppEvent,
    MmrSnapshot,
    ReplayFile,
    ReplayParseResult,
    ReplayProcessingJob,
    ResolvedRocketLeaguePaths,
    TrainingPackInstallPlan,
)


@runtime_checkable
class EventPublisherPort(Protocol):
    """Publica eventos al bus interno."""
    def publish(self, event: AppEvent) -> None: ...
    def subscribe(self, handler: Callable[[AppEvent], None]) -> None: ...


@runtime_checkable
class ReplayWatcherPort(Protocol):
    """Vigila una carpeta de replays y dispara callbacks al detectar nuevos."""
    def start(self, replay_dir: Path, on_detected: Callable[[ReplayFile], None]) -> None: ...
    def stop(self) -> None: ...
    @property
    def is_running(self) -> bool: ...


@runtime_checkable
class MmrProviderPort(Protocol):
    """Obtiene un MmrSnapshot para un epic_id y playlist dados."""
    def fetch(self, epic_id: str, playlist: str) -> MmrSnapshot: ...


@runtime_checkable
class ReplayParserPort(Protocol):
    """Parsea un .replay a JSON y extrae telemetría básica."""
    def parse(self, job: ReplayProcessingJob, output_dir: Path) -> ReplayParseResult: ...


@runtime_checkable
class StoragePort(Protocol):
    """Persiste y consulta datos de la aplicación."""
    def save_replay_job(self, job: ReplayProcessingJob) -> None: ...
    def is_replay_processed(self, sha256: str) -> bool: ...
    def save_mmr_snapshot(self, snapshot: MmrSnapshot) -> None: ...
    def save_event(self, event: AppEvent) -> None: ...
    def get_setting(self, key: str) -> str | None: ...
    def set_setting(self, key: str, value: str) -> None: ...


@runtime_checkable
class TrainingPackInstallerPort(Protocol):
    """Instala training packs con todas las validaciones de seguridad."""
    def install(self, plan: TrainingPackInstallPlan) -> bool: ...
    def dry_run(self, plan: TrainingPackInstallPlan) -> list[str]: ...


@runtime_checkable
class PathResolverPort(Protocol):
    """Resuelve y valida rutas de Rocket League y datos de RLA."""
    def resolve(self) -> ResolvedRocketLeaguePaths: ...
