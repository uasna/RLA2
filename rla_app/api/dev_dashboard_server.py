"""
RLA 2 — api/dev_dashboard_server.py
Servidor HTTP local read-only para exponer el dashboard payload al frontend.
Solo stdlib. Sin FastAPI, Flask ni uvicorn.

Uso:
    python -m rla_app.api.dev_dashboard_server
    python -m rla_app.api.dev_dashboard_server --host 127.0.0.1 --port 8765
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from rla_app.api.ui_bridge import get_dashboard_compact_payload

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8765

_CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_int(value: str, default: int, min_val: int = 1) -> int:
    try:
        result = int(value)
        return result if result >= min_val else default
    except (ValueError, TypeError):
        return default


def _json_bytes(data: dict) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


# ── Request handler ───────────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt: str, *args: object) -> None:  # suppress default stderr logs
        pass

    def _send(self, status: int, data: dict) -> None:
        body = _json_bytes(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in _CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _route(self) -> None:
        parsed   = urlparse(self.path)
        path     = parsed.path.rstrip("/")
        qs       = parse_qs(parsed.query)

        if path == "/health":
            self._handle_health()
        elif path == "/api/dashboard":
            self._handle_dashboard(qs)
        else:
            self._send(404, {"ok": False, "error": "not_found"})

    # ── GET ───────────────────────────────────────────────────────────────────

    def do_GET(self) -> None:  # noqa: N802
        self._route()

    # ── OPTIONS (CORS preflight) ──────────────────────────────────────────────

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        for k, v in _CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    # ── Endpoints ─────────────────────────────────────────────────────────────

    def _handle_health(self) -> None:
        self._send(200, {
            "ok":      True,
            "app":     "RLA2",
            "service": "dev_dashboard_server",
        })

    def _handle_dashboard(self, qs: dict) -> None:
        limit        = _parse_int(qs.get("limit",        ["50"])[0], default=50)
        recent_limit = _parse_int(qs.get("recent_limit", ["5"])[0],  default=5)

        try:
            payload = get_dashboard_compact_payload(
                limit=limit,
                recent_limit=recent_limit,
            )
            self._send(200, payload)
        except Exception as exc:  # noqa: BLE001
            self._send(500, {
                "ok":      False,
                "error":   "internal_error",
                "message": str(exc),
            })


# ── Entry point ───────────────────────────────────────────────────────────────

def _parse_args() -> tuple[str, int]:
    parser = argparse.ArgumentParser(
        description="RLA 2 — local dev dashboard HTTP server",
    )
    parser.add_argument("--host", default=_DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=_DEFAULT_PORT)
    args = parser.parse_args()
    return args.host, args.port


def main() -> None:
    host, port = _parse_args()
    server = HTTPServer((host, port), _Handler)

    print("RLA2 DEV DASHBOARD SERVER")
    print(f"Listening on http://{host}:{port}")
    print("Endpoints:")
    print("  GET /health")
    print("  GET /api/dashboard")
    print("  GET /api/dashboard?limit=N&recent_limit=N")
    print()
    print("Press Ctrl+C to stop.")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()