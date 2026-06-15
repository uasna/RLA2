"""
RLA 2 — parser/inspect_replay_json_dev.py
Inspecciona estructura de JSON header-only generado por Rattletrap --fast.

Uso:
    python -m rla_app.parser.inspect_replay_json_dev "<ruta_json>"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_INTERESTING = {"name","map","player","team","goal","score","date",
                "id","properties","frames","objects","content","body","header"}


def print_tree(value, max_depth: int = 4, max_items: int = 12, indent: int = 0) -> None:
    pad = "  " * indent
    if indent >= max_depth:
        print(f"{pad}... (max depth)")
        return
    if isinstance(value, dict):
        items = list(value.items())[:max_items]
        for k, v in items:
            typ = type(v).__name__
            if isinstance(v, (dict, list)):
                size = len(v)
                print(f"{pad}{k}: {typ}({size})")
                print_tree(v, max_depth, max_items, indent + 1)
            else:
                preview = str(v)[:80]
                print(f"{pad}{k}: {typ} = {preview}")
        if len(value) > max_items:
            print(f"{pad}... ({len(value) - max_items} more keys)")
    elif isinstance(value, list):
        print(f"{pad}list[{len(value)}]")
        if value:
            print(f"{pad}  [0]:")
            print_tree(value[0], max_depth, max_items, indent + 1)
    else:
        print(f"{pad}{type(value).__name__} = {str(value)[:80]}")


def find_interesting_keys(value, path: str = "$") -> list[str]:
    results: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            current = f"{path}.{k}"
            if any(kw in str(k).lower() for kw in _INTERESTING):
                results.append(current)
            results.extend(find_interesting_keys(v, current))
    elif isinstance(value, list) and value:
        results.extend(find_interesting_keys(value[0], f"{path}[0]"))
    return results


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m rla_app.parser.inspect_replay_json_dev <ruta_json>")
        sys.exit(1)

    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"Error: '{p}' no existe o no es archivo.")
        sys.exit(1)

    raw = p.read_text(encoding="utf-8")
    data = json.loads(raw)

    print(f"Archivo : {p}")
    print(f"Tamaño  : {p.stat().st_size:,} bytes")
    print(f"Tipo    : {type(data).__name__}")
    if isinstance(data, dict):
        print(f"Keys    : {list(data.keys())}")
    elif isinstance(data, list):
        print(f"Length  : {len(data)}")

    print("\n── TREE (depth=4, max 12 items) ─────────────────────────────")
    print_tree(data, max_depth=4, max_items=12)

    print("\n── INTERESTING KEYS ─────────────────────────────────────────")
    hits = find_interesting_keys(data)[:80]
    if hits:
        for h in hits:
            print(f"  {h}")
    else:
        print("  (ninguna)")


if __name__ == "__main__":
    main()