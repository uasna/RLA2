"""
RLA 2 — parser/replay_json_parser.py
Parsea .replay a JSON con Rattletrap. Fallback header-only si falla MissingClassName.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rla_app.parser.rattletrap_locator import get_parser_output_dir
from rla_app.parser.rattletrap_runner import run_rattletrap_command
from rla_app.storage.replay_fingerprint import compute_sha256


@dataclass
class ReplayJsonParseResult:
    ok: bool
    replay_path: Path
    json_path: Path | None
    command: list[str]
    message: str
    stdout: str
    stderr: str
    parse_level: str        # "full" | "header_only" | "none"
    fallback_used: bool
    error_type: str | None  # "missing_class_name" | "rattletrap_failed" |
                            # "invalid_replay_path" | "invalid_extension" |
                            # "json_not_created" | None


def classify_rattletrap_error(stderr: str) -> str | None:
    if "MissingClassName" in stderr:
        return "missing_class_name"
    return None


def _sha_tag(replay_path: Path) -> str:
    sha = compute_sha256(replay_path)
    return sha[:10] if sha else "nohash"


def _out(output_dir: Path | None) -> Path:
    out = output_dir or get_parser_output_dir()
    out.mkdir(parents=True, exist_ok=True)
    return out


def build_replay_json_path(replay_path: Path, output_dir: Path | None = None) -> Path:
    return _out(output_dir) / f"{replay_path.stem}_{_sha_tag(replay_path)}_full.json"


def build_replay_header_json_path(replay_path: Path, output_dir: Path | None = None) -> Path:
    return _out(output_dir) / f"{replay_path.stem}_{_sha_tag(replay_path)}_header.json"


def _fail(
    replay_path: Path, message: str, error_type: str,
    stdout: str = "", stderr: str = "",
    command: list[str] | None = None,
    fallback_used: bool = False,
) -> ReplayJsonParseResult:
    return ReplayJsonParseResult(
        ok=False, replay_path=replay_path, json_path=None,
        command=command or [], message=message,
        stdout=stdout, stderr=stderr,
        parse_level="none", fallback_used=fallback_used,
        error_type=error_type,
    )


def parse_replay_to_json(
    replay_path: Path,
    output_dir: Path | None = None,
    compact: bool = True,
    timeout_seconds: float = 120.0,
) -> ReplayJsonParseResult:
    if not replay_path.is_file():
        return _fail(replay_path, f"No encontrado: {replay_path}", "invalid_replay_path")
    if replay_path.suffix.lower() != ".replay":
        return _fail(replay_path, f"Extensión inválida: {replay_path.suffix}", "invalid_extension")

    full_json   = build_replay_json_path(replay_path, output_dir)
    header_json = build_replay_header_json_path(replay_path, output_dir)

    # ── Full JSON ya existe ───────────────────────────────────────────────────
    if full_json.exists():
        return ReplayJsonParseResult(
            ok=True, replay_path=replay_path, json_path=full_json, command=[],
            message="Full JSON already exists", stdout="", stderr="",
            parse_level="full", fallback_used=False, error_type=None,
        )

    # ── Intentar full decode ──────────────────────────────────────────────────
    args = ["--mode", "decode", "--input", str(replay_path), "--output", str(full_json)]
    if compact:
        args.append("--compact")

    r = run_rattletrap_command(args, timeout_seconds=timeout_seconds)

    if r.ok and full_json.exists():
        return ReplayJsonParseResult(
            ok=True, replay_path=replay_path, json_path=full_json, command=r.command,
            message="Parsed full OK", stdout=r.stdout, stderr=r.stderr,
            parse_level="full", fallback_used=False, error_type=None,
        )

    # ── Clasificar error del full decode ─────────────────────────────────────
    err_type = classify_rattletrap_error(r.stderr)

    if err_type != "missing_class_name":
        et = "json_not_created" if r.ok else "rattletrap_failed"
        msg = "Rattletrap OK pero full JSON no fue creado." if r.ok else r.message
        return _fail(replay_path, msg, et, r.stdout, r.stderr, r.command)

    # ── Fallback header-only con --fast ───────────────────────────────────────
    if header_json.exists():
        return ReplayJsonParseResult(
            ok=True, replay_path=replay_path, json_path=header_json, command=[],
            message="Header JSON already exists after full decode failed",
            stdout="", stderr="",
            parse_level="header_only", fallback_used=True,
            error_type="missing_class_name",
        )

    hargs = ["--mode", "decode", "--fast",
             "--input", str(replay_path), "--output", str(header_json)]
    if compact:
        hargs.append("--compact")

    hr = run_rattletrap_command(hargs, timeout_seconds=timeout_seconds)

    if hr.ok and header_json.exists():
        return ReplayJsonParseResult(
            ok=True, replay_path=replay_path, json_path=header_json, command=hr.command,
            message="Parsed header-only OK after full decode failed",
            stdout=hr.stdout, stderr=hr.stderr,
            parse_level="header_only", fallback_used=True,
            error_type="missing_class_name",
        )

    return _fail(replay_path, hr.message, "rattletrap_failed",
                 hr.stdout, hr.stderr, hr.command, fallback_used=True)