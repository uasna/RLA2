"""
RLA 2 — parser/inspect_header_properties_dev.py
Inspecciona header.body.properties.elements de un JSON header-only de Rattletrap.

Uso:
    python -m rla_app.parser.inspect_header_properties_dev "<ruta_json_header>"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_KNOWN_KEYS = ("key", "name", "kind", "type", "value", "property",
               "object", "str", "int", "float", "bool")


def compact_preview(value, max_chars: int = 160) -> str:
    s = str(value).replace("\n", " ").replace("\r", "")
    return s[:max_chars] + ("…" if len(s) > max_chars else "")


def print_property_element(index: int, element) -> None:
    print(f"\n── [{index}] ─────────────────────────────────────────────")
    print(f"  tipo raíz : {type(element).__name__}")

    if isinstance(element, dict):
        print(f"  keys      : {list(element.keys())}")
        print(f"  contenido : {compact_preview(element)}")
        found = {k: element[k] for k in _KNOWN_KEYS if k in element}
        if found:
            print("  campos conocidos:")
            for k, v in found.items():
                print(f"    {k}: {compact_preview(v, 120)}")
    else:
        print(f"  contenido : {compact_preview(element)}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m rla_app.parser.inspect_header_properties_dev <ruta_json>")
        sys.exit(1)

    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"Error: '{p}' no existe o no es archivo.")
        sys.exit(1)

    data = json.loads(p.read_text(encoding="utf-8"))

    try:
        elements = data["header"]["body"]["properties"]["elements"]
        if not isinstance(elements, list):
            raise TypeError("elements no es list")
    except (KeyError, TypeError) as exc:
        print(f"Error: no se encontró header.body.properties.elements — {exc}")
        sys.exit(2)

    print(f"Archivo     : {p}")
    print(f"Properties  : {len(elements)} elementos")

    for i, el in enumerate(elements):
        print_property_element(i, el)

    print(f"\n── FIN ({len(elements)} properties) ────────────────────────")


if __name__ == "__main__":
    main()