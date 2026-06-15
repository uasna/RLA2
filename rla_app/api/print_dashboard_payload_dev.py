"""
RLA 2 — api/print_dashboard_payload_dev.py
Imprime el payload de UI como JSON. Mock para Electron/Tauri.

Uso:
    python -m rla_app.api.print_dashboard_payload_dev
    python -m rla_app.api.print_dashboard_payload_dev 5
"""
from __future__ import annotations

import json
import sys

from rla_app.api.ui_bridge import get_dashboard_payload


def main() -> None:
    limit = 20
    if len(sys.argv) >= 2:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            limit = 20

    payload = get_dashboard_payload(limit)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()