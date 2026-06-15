# rla_app/api/live_export_dashboard_payload_dev.py
"""
Dev script: exports compact dashboard payload periodically.
Usage:
    python -m rla_app.api.live_export_dashboard_payload_dev
    python -m rla_app.api.live_export_dashboard_payload_dev 50 5 5
    python -m rla_app.api.live_export_dashboard_payload_dev 50 5 5 frontend/public/dashboard_payload.json
"""

import sys
import time
from pathlib import Path

from rla_app.api.export_dashboard_compact_payload_dev import export_payload

DEFAULT_LIMIT = 50
DEFAULT_RECENT_LIMIT = 5
DEFAULT_INTERVAL = 5.0
DEFAULT_OUTPUT = "frontend/public/dashboard_payload.json"


def parse_args() -> tuple[int, int, float, Path]:
    args = sys.argv[1:]

    try:
        limit = int(args[0])
    except (IndexError, ValueError):
        limit = DEFAULT_LIMIT

    try:
        recent_limit = int(args[1])
    except (IndexError, ValueError):
        recent_limit = DEFAULT_RECENT_LIMIT

    try:
        interval = float(args[2])
        if interval < 1:
            interval = DEFAULT_INTERVAL
    except (IndexError, ValueError):
        interval = DEFAULT_INTERVAL

    try:
        output_path = Path(args[3])
    except IndexError:
        output_path = Path(DEFAULT_OUTPUT)

    return limit, recent_limit, interval, output_path


def main() -> None:
    limit, recent_limit, interval, output_path = parse_args()

    print("LIVE DASHBOARD EXPORTER")
    print(f"output: {output_path}")
    print(f"limit: {limit}")
    print(f"recent_limit: {recent_limit}")
    print(f"interval_seconds: {interval}")
    print("Press Ctrl+C to stop.")
    print()

    try:
        while True:
            export_payload(limit, recent_limit, output_path)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Stopped live exporter.")
        sys.exit(0)


if __name__ == "__main__":
    main()