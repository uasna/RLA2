"""
RLA 2 — api/smoke_ui_payload_dev.py
Smoke test único del puente UI: normalizer + payload + validator.

Uso:
    python -m rla_app.api.smoke_ui_payload_dev
    python -m rla_app.api.smoke_ui_payload_dev 50 5
"""
from __future__ import annotations

import sys

from rla_app.api.ui_bridge import get_dashboard_compact_payload
from rla_app.api.validate_dashboard_compact_payload_dev import validate
from rla_app.domain.map_names import normalize_map_name

# ── Casos de prueba del normalizador ─────────────────────────────────────────

_MAP_CASES: list[tuple[str | None, str]] = [
    ("cs_day_p",      "CS Day"),
    ("stadium_day_p", "Stadium Day"),
    ("UF_Day_P",      "UF Day"),
    ("FF_Dusk_P",     "FF Dusk"),
    ("Farm_GRS_P",    "Farm GRS"),
    ("STADIUM_10A_P", "Stadium 10A"),
    (None,            "Unknown Map"),
]


def main() -> None:
    limit, recent_limit = 50, 5

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

    errors: list[str] = []

    # ── 1. Probar normalizador de mapas ───────────────────────────────────────
    for raw, expected in _MAP_CASES:
        actual = normalize_map_name(raw).display_name
        if actual != expected:
            errors.append(f"map normalizer: '{raw}' expected '{expected}' got '{actual}'")

    # ── 2. Construir payload ──────────────────────────────────────────────────
    payload = get_dashboard_compact_payload(limit, recent_limit)

    # ── 3. Validar payload ────────────────────────────────────────────────────
    for err in validate(payload):
        errors.append(f"payload: {err}")

    # ── 4. Imprimir resumen ───────────────────────────────────────────────────
    ss  = payload.get("system_status", {})
    sum_= payload.get("summary", {})
    sm  = payload.get("session_summary", {})

    latest_map   = sm.get("latest_display_map") or sm.get("latest_map") or "—"
    latest_type  = sm.get("latest_match_type")  or "—"
    latest_score = sm.get("latest_score_label") or "—"
    total        = sum_.get("total_loaded", 0)
    meta_ready   = sum_.get("metadata_ready", 0)

    print("RLA2 UI PAYLOAD SMOKE TEST")
    print(f"state          : {ss.get('state', '—')}")
    print(f"loaded         : {total}")
    print(f"metadata       : {meta_ready}/{total}")
    print(f"active_session : {ss.get('active_session_count', 0)}")
    print(f"recent_matches : {len(payload.get('recent_matches', []))}")
    print(f"latest         : {latest_map} · {latest_type} · {latest_score}")
    print()

    if errors:
        print("SMOKE TEST FAILED")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("SMOKE TEST OK")
        sys.exit(0)


if __name__ == "__main__":
    main()