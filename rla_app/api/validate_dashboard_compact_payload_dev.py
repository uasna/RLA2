"""
RLA 2 — api/validate_dashboard_compact_payload_dev.py
Valida que el payload compacto tenga las keys mínimas esperadas por la UI.

Uso:
    python -m rla_app.api.validate_dashboard_compact_payload_dev
    python -m rla_app.api.validate_dashboard_compact_payload_dev 50 5
"""
from __future__ import annotations

import sys

from rla_app.api.ui_bridge import get_dashboard_compact_payload

# ── Conjuntos de validación ───────────────────────────────────────────────────

REQUIRED_TOP_KEYS = {
    "app", "database", "summary", "snapshot", "session_summary",
    "system_status", "metric_cards", "active_session_matches", "recent_matches",
}

REQUIRED_SYSTEM_STATUS_KEYS = {
    "state", "message", "has_matches", "has_active_session",
    "total_loaded", "metadata_ready", "metadata_missing", "latest_match_date",
    "latest_map", "latest_display_map", "latest_match_type", "latest_parse_level",
    "latest_metadata_ready", "active_session_count",
}

VALID_STATES = {"Ready", "Partial", "Awaiting replay"}

REQUIRED_METRIC_CARD_KEYS = {"id", "label", "value", "sublabel", "tone"}

VALID_TONES = {"neutral", "success", "warning"}

REQUIRED_MATCH_KEYS = {
    "id", "file_name", "status", "parse_status", "parse_level", "meta_status",
    "date", "map_name", "match_type", "team_size", "team0_score", "team1_score",
    "total_seconds_played", "replay_name", "score_label", "seconds_label",
    "metadata_ready", "display_map_name", "short_map_name", "map_family",
    "map_variant", "map_name_source",
}

VALID_MAP_NAME_SOURCES = {"known", "fallback", "missing"}


# ── Helpers de validación ─────────────────────────────────────────────────────

def _check_keys(obj: dict, required: set[str], context: str, errors: list[str]) -> None:
    missing = required - obj.keys()
    for key in sorted(missing):
        errors.append(f"{context}: missing key '{key}'")


def _validate_match_list(matches: list, label: str, errors: list[str]) -> None:
    for i, m in enumerate(matches):
        if not isinstance(m, dict):
            errors.append(f"{label}[{i}]: not a dict")
            continue
        _check_keys(m, REQUIRED_MATCH_KEYS, f"{label}[{i}]", errors)
        if "map_name_source" in m and m["map_name_source"] not in VALID_MAP_NAME_SOURCES:
            errors.append(
                f"{label}[{i}].map_name_source: invalid value '{m['map_name_source']}'"
            )


# ── Validador principal ───────────────────────────────────────────────────────

def validate(payload: dict) -> list[str]:
    errors: list[str] = []

    # Top-level keys
    _check_keys(payload, REQUIRED_TOP_KEYS, "payload", errors)

    # "matches" must NOT exist in compact payload
    if "matches" in payload:
        errors.append("payload: forbidden key 'matches' found in compact payload")

    # system_status
    ss = payload.get("system_status")
    if not isinstance(ss, dict):
        errors.append("system_status: not a dict")
    else:
        _check_keys(ss, REQUIRED_SYSTEM_STATUS_KEYS, "system_status", errors)
        state = ss.get("state")
        if state not in VALID_STATES:
            errors.append(f"system_status.state: invalid value '{state}'")

    # metric_cards
    cards = payload.get("metric_cards")
    if not isinstance(cards, list):
        errors.append("metric_cards: not a list")
    else:
        for i, card in enumerate(cards):
            if not isinstance(card, dict):
                errors.append(f"metric_cards[{i}]: not a dict")
                continue
            _check_keys(card, REQUIRED_METRIC_CARD_KEYS, f"metric_cards[{i}]", errors)
            if "tone" in card and card["tone"] not in VALID_TONES:
                errors.append(f"metric_cards[{i}].tone: invalid value '{card['tone']}'")

    # recent_matches
    rm = payload.get("recent_matches")
    if not isinstance(rm, list):
        errors.append("recent_matches: not a list")
    else:
        _validate_match_list(rm, "recent_matches", errors)

    # active_session_matches
    asm = payload.get("active_session_matches")
    if not isinstance(asm, list):
        errors.append("active_session_matches: not a list")
    else:
        _validate_match_list(asm, "active_session_matches", errors)

    return errors


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    limit, recent_limit = 50, 10
    if len(sys.argv) >= 2:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
    if len(sys.argv) >= 3:
        try:
            recent_limit = int(sys.argv[2])
        except ValueError:
            pass

    payload = get_dashboard_compact_payload(limit, recent_limit)
    errors  = validate(payload)

    if errors:
        print("VALIDATION FAILED")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("VALIDATION OK")
        sys.exit(0)


if __name__ == "__main__":
    main()