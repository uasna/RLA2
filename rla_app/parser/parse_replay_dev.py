"""
RLA 2 — parser/parse_replay_dev.py
Parsea un replay individual desde terminal.

Uso:
    python -m rla_app.parser.parse_replay_dev "<ruta_replay>"
    python -m rla_app.parser.parse_replay_dev "<ruta_replay>" "tmp/parsed"
"""
from __future__ import annotations

import sys
from pathlib import Path

from rla_app.parser.replay_json_parser import parse_replay_to_json


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m rla_app.parser.parse_replay_dev <replay> [output_dir]")
        sys.exit(1)

    replay_path = Path(sys.argv[1])
    output_dir  = Path(sys.argv[2]) if len(sys.argv) >= 3 else None

    r = parse_replay_to_json(replay_path, output_dir=output_dir)

    print(f"Replay      : {r.replay_path}")
    print(f"ok          : {r.ok}")
    print(f"parse_level : {r.parse_level}")
    print(f"fallback    : {r.fallback_used}")
    print(f"error_type  : {r.error_type}")
    print(f"message     : {r.message}")
    print(f"json_path   : {r.json_path}")
    print(f"command     : {' '.join(r.command) if r.command else '—'}")

    if r.stderr:
        print(f"\nstderr (500c):\n{r.stderr[:500]}")

    sys.exit(0 if r.ok else 2)


if __name__ == "__main__":
    main()