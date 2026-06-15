"""
RLA 2 — parser/parse_folder_store_dev.py
Parsea carpeta de replays y persiste resultado en SQLite.

Uso:
    python -m rla_app.parser.parse_folder_store_dev "<carpeta>"
    python -m rla_app.parser.parse_folder_store_dev "<carpeta>" "tmp/parsed"
"""
from __future__ import annotations

import sys
from pathlib import Path

from rla_app.parser.replay_json_parser import parse_replay_to_json
from rla_app.storage.db_location import get_default_db_path
from rla_app.storage.sqlite_store import ReplayStore


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m rla_app.parser.parse_folder_store_dev <carpeta> [output_dir]")
        sys.exit(1)

    folder = Path(sys.argv[1])
    if not folder.is_dir():
        print(f"Error: '{folder}' no existe o no es una carpeta.")
        sys.exit(1)

    output_dir = Path(sys.argv[2]) if len(sys.argv) >= 3 else None
    db_path    = get_default_db_path()
    store      = ReplayStore(db_path)
    replays    = sorted(folder.glob("*.replay"))

    if not replays:
        print("No hay replays en la carpeta.")
        sys.exit(0)

    ok_count = full = header_only = failed = 0
    new_in_db = sql_ok = sql_fail = 0

    for path in replays:
        # Registrar si falta en DB
        if store.get_replay_by_path(path) is None:
            store.add_replay(path, status="indexed_for_parse")
            new_in_db += 1

        r = parse_replay_to_json(path, output_dir=output_dir)

        stored = store.update_parse_result(
            path, r.ok, r.parse_level, r.json_path, r.error_type, r.message
        )
        if stored:
            sql_ok += 1
        else:
            sql_fail += 1

        if r.ok:
            ok_count += 1
            full        += r.parse_level == "full"
            header_only += r.parse_level == "header_only"
            print(f"[OK]   {path.name} | {r.parse_level} | "
                  f"fallback={r.fallback_used} | {r.error_type} | stored={stored}")
        else:
            failed += 1
            print(f"[FAIL] {path.name} | {r.parse_level} | "
                  f"fallback={r.fallback_used} | {r.error_type} | stored={stored} | {r.message}")

    print(f"\n── Resumen ──────────────────────────────────")
    print(f"  DB              : {db_path}")
    print(f"  Carpeta         : {folder}")
    print(f"  Encontrados     : {len(replays)}")
    print(f"  OK              : {ok_count}")
    print(f"    full          : {full}")
    print(f"    header_only   : {header_only}")
    print(f"  Fallidos        : {failed}")
    print(f"  Nuevos en DB    : {new_in_db}")
    print(f"  Updates SQL OK  : {sql_ok}")
    print(f"  Updates SQL FAIL: {sql_fail}")

    sys.exit(0 if failed == 0 and sql_fail == 0 else 2)


if __name__ == "__main__":
    main()