"""
RLA 2 — parser/rattletrap_runner.py
Invocador seguro de Rattletrap via subprocess.
Solo stdlib. Sin shell=True. Sin parseo de archivos.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from rla_app.parser.rattletrap_locator import find_rattletrap


@dataclass
class RattletrapRunResult:
    ok: bool
    returncode: int | None
    stdout: str
    stderr: str
    command: list[str]
    message: str


def run_rattletrap_command(
    args: list[str],
    timeout_seconds: float = 20.0,
) -> RattletrapRunResult:
    info = find_rattletrap()
    if not info.found:
        return RattletrapRunResult(
            ok=False, returncode=None,
            stdout="", stderr="",
            command=[], message=info.message,
        )

    cmd = [str(info.path), *args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        ok = result.returncode == 0
        return RattletrapRunResult(
            ok=ok,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            command=cmd,
            message="OK" if ok else f"Rattletrap returned code {result.returncode}",
        )
    except subprocess.TimeoutExpired as exc:
        return RattletrapRunResult(
            ok=False, returncode=None,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            command=cmd,
            message=f"Timeout tras {timeout_seconds}s ejecutando Rattletrap.",
        )
    except Exception as exc:  # noqa: BLE001
        return RattletrapRunResult(
            ok=False, returncode=None,
            stdout="", stderr="",
            command=cmd,
            message=f"Error inesperado: {exc}",
        )


def run_rattletrap_help() -> RattletrapRunResult:
    return run_rattletrap_command(["--help"], timeout_seconds=10.0)


def run_rattletrap_version() -> RattletrapRunResult:
    return run_rattletrap_command(["--version"], timeout_seconds=10.0)