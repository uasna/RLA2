"""
RLA 2 — parser/parse_folder_dev.py
Parsea todos los .replay de una carpeta.

Uso:
    python -m rla_app.parser.parse_folder_dev "<carpeta>"
    python -m rla_app.parser.parse_folder_dev "<carpeta>" "tmp/parsed"
"""
from __future__ import annotations

import sys
from pathlib import Path

from rla_app.parser.replay_json_parser import parse_replay_to_json


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m rla_app.parser.parse_folder_dev <carpeta> [output_dir]")
        sys.exit(1)

    folder = Path(sys.argv[1])
    if not folder.is_dir():
        print(f"Error: '{folder}' no existe o no es una carpeta.")
        sys.exit(1)

    output_dir = Path(sys.argv[2]) if len(sys.argv) >= 3 else None
    replays = sorted(folder.glob("*.replay"))

    if not replays:
        print("No hay replays en la carpeta.")
        sys.exit(0)

    ok_count = full = header_only = failed = 0

    for path in replays:
        r = parse_replay_to_json(path, output_dir=output_dir)
        json_name = r.json_path.name if r.json_path else "—"

        if r.ok:
            ok_count += 1
            if r.parse_level == "full":
                full += 1
            else:
                header_only += 1
            print(f"[OK]   {path.name} | {r.parse_level} | "
                  f"fallback={r.fallback_used} | {r.error_type} | {json_name}")
        else:
            failed += 1
            print(f"[FAIL] {path.name} | {r.parse_level} | "
                  f"fallback={r.fallback_used} | {r.error_type} | {r.message}")

    print(f"\n── Resumen ──────────────────────────────")
    print(f"  Carpeta      : {folder}")
    print(f"  Encontrados  : {len(replays)}")
    print(f"  OK           : {ok_count}")
    print(f"    full       : {full}")
    print(f"    header_only: {header_only}")
    print(f"  Fallidos     : {failed}")

    sys.exit(0 if failed == 0 else 2)


if __name__ == "__main__":
    main()