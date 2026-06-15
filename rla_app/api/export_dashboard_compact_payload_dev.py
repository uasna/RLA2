"""
RLA 2 — api/export_dashboard_compact_payload_dev.py

Exports compact dashboard payload to frontend/public/dashboard_payload.json.

Usage:
    python -m rla_app.api.export_dashboard_compact_payload_dev
    python -m rla_app.api.export_dashboard_compact_payload_dev 50 5
    python -m rla_app.api.export_dashboard_compact_payload_dev 50 5 frontend/public/dashboard_payload.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rla_app.api.ui_bridge import get_dashboard_compact_payload

DEFAULT_LIMIT = 50
DEFAULT_RECENT_LIMIT = 5
DEFAULT_OUTPUT = "frontend/public/dashboard_payload.json"


def _parse_int_arg(args: list[str], index: int, default: int) -> int:
    try:
        return int(args[index])
    except (IndexError, ValueError):
        return default


def parse_args() -> tuple[int, int, Path]:
    args = sys.argv[1:]

    limit = _parse_int_arg(args, 0, DEFAULT_LIMIT)
    recent_limit = _parse_int_arg(args, 1, DEFAULT_RECENT_LIMIT)
    output_path = Path(args[2]) if len(args) > 2 else Path(DEFAULT_OUTPUT)

    return limit, recent_limit, output_path


def export_payload(limit: int, recent_limit: int, output_path: Path) -> None:
    payload = get_dashboard_compact_payload(limit=limit, recent_limit=recent_limit)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = payload.get("summary", {})
    system_status = payload.get("system_status", {})
    recent = payload.get("recent_matches", [])
    active = payload.get("active_session_matches", [])

    print("EXPORTED DASHBOARD PAYLOAD")
    print(f"path          : {output_path.resolve()}")
    print(f"state         : {system_status.get('state', 'unknown')}")
    print(f"loaded        : {summary.get('total_loaded', '?')}")
    print(f"recent_matches: {len(recent)}")
    print(f"active_session: {system_status.get('active_session_count', len(active))}")


def main() -> None:
    limit, recent_limit, output_path = parse_args()
    export_payload(limit, recent_limit, output_path)


if __name__ == "__main__":
    main()