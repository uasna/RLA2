"""
RLA 2 — replay_intake/replay_event_handler.py
Valida, espera estabilidad, parsea, extrae metadata y persiste un replay detectado.
"""
from __future__ import annotations

from pathlib import Path

from rla_app.parser.replay_header_metadata import extract_replay_header_metadata
from rla_app.parser.replay_json_parser import parse_replay_to_json
from rla_app.replay_intake.replay_detector import describe_replay_candidate
from rla_app.utils.file_stability import wait_for_file_stability


def _publish(bus, category: str, message: str, payload: dict | None = None) -> None:
    payload = payload or {}
    for method_name in ("publish", "emit"):
        method = getattr(bus, method_name, None)
        if method is None:
            continue
        for call in (
            lambda m=method: m(category=category, message=message, payload=payload),
            lambda m=method: m(category, message, payload),
            lambda m=method: m(category, message),
        ):
            try:
                call()
                return
            except TypeError:
                continue


def _get_row(store, path: Path) -> dict | None:
    fn = getattr(store, "get_replay_by_path", None)
    return fn(path) if fn else None


def _row_has_parse(row: dict | None) -> bool:
    return bool(row and row.get("parse_status"))


def handle_replay_file(
    path: Path,
    event_bus,
    replay_store=None,
    stability_checks: int = 2,
    stability_interval: float = 1.0,
    stability_timeout: float = 15.0,
) -> bool:
    try:
        # ── 1. Validar candidato ──────────────────────────────────────────────
        reason = describe_replay_candidate(path)
        if reason != "valid_replay":
            _publish(event_bus, "REPLAY_IGNORED",
                     f"Ignorado ({reason}): {path.name}",
                     {"path": str(path), "reason": reason})
            return False

        # ── 2. Verificar duplicado ────────────────────────────────────────────
        already_in_db = False
        if replay_store is not None and replay_store.has_replay(path):
            row = _get_row(replay_store, path)
            if row is None:
                _publish(event_bus, "REPLAY_ALREADY_PROCESSED",
                         f"Ya existe por path o sha, sin fila para esta ruta: {path.name}",
                         {"path": str(path)})
                return False
            if _row_has_parse(row):
                _publish(event_bus, "REPLAY_ALREADY_PROCESSED",
                         f"Ya procesado: {path.name}", {"path": str(path)})
                return False
            already_in_db = True

        # ── 3. Detectar y esperar estabilidad ─────────────────────────────────
        _publish(event_bus, "REPLAY_DETECTED",
                 f"Replay detectado: {path.name}", {"path": str(path)})

        if not wait_for_file_stability(path, stability_checks,
                                       stability_interval, stability_timeout):
            _publish(event_bus, "REPLAY_NOT_STABLE",
                     f"Timeout estabilidad: {path.name}", {"path": str(path)})
            return False

        _publish(event_bus, "REPLAY_STABLE",
                 f"Replay estable: {path.name}", {"path": str(path)})

        # ── 4. Registrar en DB si falta ───────────────────────────────────────
        if replay_store is not None and not already_in_db:
            inserted = replay_store.add_replay(path, status="stable")
            if not inserted:
                row = _get_row(replay_store, path)
                if row is None:
                    _publish(event_bus, "REPLAY_ALREADY_PROCESSED",
                             f"Duplicado SHA sin fila: {path.name}", {"path": str(path)})
                    return False
                if _row_has_parse(row):
                    _publish(event_bus, "REPLAY_ALREADY_PROCESSED",
                             f"Race condition, ya procesado: {path.name}", {"path": str(path)})
                    return False
            else:
                _publish(event_bus, "REPLAY_REGISTERED",
                         f"Registrado: {path.name}", {"path": str(path)})

        # ── 5. Parsear ────────────────────────────────────────────────────────
        _publish(event_bus, "REPLAY_PARSE_STARTED",
                 f"Iniciando parseo: {path.name}", {"path": str(path)})

        pr = parse_replay_to_json(path)

        stored = False
        if replay_store is not None:
            stored = bool(replay_store.update_parse_result(
                path, pr.ok, pr.parse_level, pr.json_path,
                pr.error_type, pr.message,
            ))

        if not pr.ok:
            _publish(event_bus, "REPLAY_PARSE_FAILED",
                     f"Parseo falló: {path.name}",
                     {"path": str(path), "parse_level": pr.parse_level,
                      "fallback_used": pr.fallback_used, "error_type": pr.error_type,
                      "message": pr.message, "stored": stored})
            return False

        # ── 6. Extraer metadata ───────────────────────────────────────────────
        metadata_ok = False
        metadata_stored = False
        meta_payload: dict = {
    "map_name": None,
    "match_type": None,
    "date": None,
    "team_size": None,
    "team0_score": None,
    "team1_score": None,
    "total_seconds_played": None,
}
        if pr.json_path is None:
            _publish(event_bus, "REPLAY_METADATA_FAILED",
                     f"json_path ausente: {path.name}",
                     {"path": str(path), "reason": "missing_json_path"})
        else:
            try:
                _publish(event_bus, "REPLAY_METADATA_STARTED",
                         f"Extrayendo metadata: {path.name}",
                         {"path": str(path), "json_path": str(pr.json_path)})

                meta = extract_replay_header_metadata(pr.json_path)

                if replay_store is not None:
                    metadata_stored = bool(
                        replay_store.update_header_metadata(path, meta)
                    )

                if meta.ok:
                    metadata_ok = True
                    meta_payload = {
                        "map_name":             meta.map_name,
                        "match_type":           meta.match_type,
                        "date":                 meta.date,
                        "team_size":            meta.team_size,
                        "team0_score":          meta.team0_score,
                        "team1_score":          meta.team1_score,
                        "total_seconds_played": meta.total_seconds_played,
                    }
                    _publish(event_bus, "REPLAY_METADATA_DONE",
                             f"Metadata OK: {path.name}",
                             {"path": str(path), "json_path": str(pr.json_path),
                              "metadata_stored": metadata_stored, **meta_payload})
                else:
                    _publish(event_bus, "REPLAY_METADATA_FAILED",
                             f"Metadata falló: {path.name}",
                             {"path": str(path), "json_path": str(pr.json_path),
                              "message": meta.message, "metadata_stored": metadata_stored})

            except Exception as exc:  # noqa: BLE001
                _publish(event_bus, "REPLAY_METADATA_FAILED",
                         f"Error inesperado en metadata: {exc}",
                         {"path": str(path)})

        # ── 7. Evento final ───────────────────────────────────────────────────
        _publish(event_bus, "REPLAY_PARSE_DONE",
                 f"Parseo OK ({pr.parse_level}): {path.name}",
                 {"path": str(path), "json_path": str(pr.json_path),
                  "parse_level": pr.parse_level, "fallback_used": pr.fallback_used,
                  "error_type": pr.error_type, "stored": stored,
                  "metadata_ok": metadata_ok, "metadata_stored": metadata_stored,
                  **meta_payload})
        return True

    except Exception as exc:  # noqa: BLE001
        _publish(event_bus, "ERROR", f"Error inesperado: {path}: {exc}")
        return False