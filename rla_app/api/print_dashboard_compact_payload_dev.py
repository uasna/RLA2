"""
RLA 2 — api/print_dashboard_compact_payload_dev.py
Imprime el payload compacto de UI como JSON. Mock para Electron/Tauri.

Uso:
    python -m rla_app.api.print_dashboard_compact_payload_dev
    python -m rla_app.api.print_dashboard_compact_payload_dev 50 5
"""
from __future__ import annotations

import json
import sys

from rla_app.api.ui_bridge import get_dashboard_compact_payload


def main() -> None:
    limit        = 50
    recent_limit = 10

    if len(sys.argv) >= 2:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            limit = 50

    if len(sys.argv) >= 3:
        try:
            recent_limit = int(sys.argv[2])
        except ValueError:
            recent_limit = 10

    payload = get_dashboard_compact_payload(limit, recent_limit)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()