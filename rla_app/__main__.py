"""
RLA 2 — __main__.py
Punto de entrada: python -m rla_app

En Punto 1 solo ejecuta el Path Resolver y muestra diagnóstico.
Los módulos adicionales se irán activando en puntos posteriores.
"""
from __future__ import annotations

import logging
import sys

from rla_app.app.event_bus import get_bus
from rla_app.config.paths import RLPathResolver
from rla_app.core.models import AppEventCategory, AppEventLevel
from rla_app.utils.logging import setup_logging


def main() -> int:
    # ── Logging básico a consola (sin carpeta aún) ────────────────────────────
    setup_logging(log_dir=None, level=logging.DEBUG)
    bus = get_bus()

    bus.info(AppEventCategory.SYSTEM, "RLA 2 arrancando — Punto 1: Path Resolver")

    # ── Resolver rutas ────────────────────────────────────────────────────────
    resolver = RLPathResolver()
    paths = resolver.resolve()

    # Emitir eventos según resultado
    if paths.errors:
        for err in paths.errors:
            bus.error(AppEventCategory.PATHS, err)
    else:
        bus.info(AppEventCategory.PATHS, "PATHS_RESOLVED — todas las rutas críticas OK")

    for warn in paths.warnings:
        bus.warning(AppEventCategory.PATHS, warn)

    # ── Imprimir diagnóstico completo ─────────────────────────────────────────
    print()
    for line in paths.summary_lines():
        print(line)
    print()

    # ── Detalle de todos los candidatos probados ──────────────────────────────
    print("── REPLAY CANDIDATES ───────────────────────────────")
    for probe in paths.probed_replays:
        mark = "✓" if probe.exists else "✗"
        print(f"  {mark} [{probe.label}]")
        print(f"      {probe.path}")
    print()

    print("── LOG CANDIDATES ──────────────────────────────────")
    for probe in paths.probed_logs:
        mark = "✓" if probe.exists else "✗"
        print(f"  {mark} [{probe.label}]")
        print(f"      {probe.path}")
    print()

    print("── TRAINING CANDIDATES ─────────────────────────────")
    for probe in paths.probed_training:
        mark = "✓" if probe.exists else "✗"
        print(f"  {mark} [{probe.label}]")
        print(f"      {probe.path}")
    print()

    print("── APP DATA STRUCTURE ──────────────────────────────")
    print(f"  Root      : {paths.app_data_dir}")
    print(f"  DB        : {paths.app_db_path}")
    print(f"  Logs      : {paths.app_logs_dir}")
    print(f"  JSON out  : {paths.app_replay_json_dir}")
    print(f"  Cache     : {paths.app_cache_dir}")
    print(f"  Train bank: {paths.app_training_bank_dir}")
    print()

    bus.info(AppEventCategory.SYSTEM, "Punto 1 completo. Esperando confirmación para Punto 2.")
    return 0 if not paths.errors else 1


if __name__ == "__main__":
    sys.exit(main())
