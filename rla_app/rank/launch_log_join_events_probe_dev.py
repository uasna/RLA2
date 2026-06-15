"""
Dev diagnostic: scans RL log files for join/matchmaking events.

Usage:
    python -m rla_app.rank.launch_log_join_events_probe_dev
    python -m rla_app.rank.launch_log_join_events_probe_dev --limit-files 10
    python -m rla_app.rank.launch_log_join_events_probe_dev --logs-dir "C:\\path\\Logs"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


LOG_DIR_CANDIDATES = [
    Path.home() / "OneDrive" / "Documents" / "My Games" / "Rocket League" / "TAGame" / "Logs",
    Path.home() / "Documents" / "My Games" / "Rocket League" / "TAGame" / "Logs",
]

OUTPUT_DIR = Path.home() / "Documents" / "My Games" / "RLA" / "logs"
OUTPUT_TXT = OUTPUT_DIR / "launch_log_join_events_probe.txt"
OUTPUT_JSON = OUTPUT_DIR / "launch_log_join_events_probe.json"

TRIGGER_KEYWORDS = [
    "JoinSettings=",
    "CheckReservation",
    "StartJoin",
    "TryToPlayOnlineWithAntiCheat",
    "HandleServerReserved",
    "OnlineGameMatchmaking",
    "OnlineGamePrivateMatch",
    "RankedReconnect",
]

RE_LOG_TIME = re.compile(r"^\[(\d+\.\d+)\]")
RE_PLAYLIST = re.compile(r"PlaylistId=\(?(\d+)\)?|Playlist=\(?(\d+)\)?", re.IGNORECASE)
RE_MATCH_TYPE = re.compile(r"MatchType=([A-Za-z0-9_]+)", re.IGNORECASE)
RE_REGION = re.compile(r'Region="?([^",\s]+)"?', re.IGNORECASE)
RE_SERVER = re.compile(r'ServerName="([^"]*)"', re.IGNORECASE)


REDACT_PATTERNS = [
    (re.compile(r'DSRToken="[^"]*"'), 'DSRToken="<redacted>"'),
    (re.compile(r'JoinCredentials="[^"]*"'), 'JoinCredentials="<redacted>"'),
    (re.compile(r'ReservationID="[^"]*"'), 'ReservationID="<redacted>"'),
    (re.compile(r'JoinPassword="[^"]*"'), 'JoinPassword="<redacted>"'),
    (re.compile(r'Password="[^"]*"'), 'Password="<redacted>"'),
    (re.compile(r'JoinName="[^"]*"'), 'JoinName="<redacted>"'),
    (re.compile(r'\(Epic\|[^|]+\|'), '(Epic|<redacted>|'),
    (re.compile(r'eyJ[A-Za-z0-9._-]{20,}'), '<jwt_redacted>'),
]

def classify_event(line: str) -> str:
    lower = line.lower()

    if "rankedreconnect" in lower:
        return "RankedReconnect"
    if "onlinegamematchmaking" in lower:
        return "Matchmaking"
    if "onlinegameprivatematch" in lower:
        return "PrivateMatch"
    if "handleserverreserved" in lower:
        return "ServerReserved"
    if "checkreservation" in lower:
        return "CheckReservation"
    if "startjoin" in lower:
        return "StartJoin"
    if "trytoplayonline" in lower:
        return "TryToPlayOnline"
    if "joinsettings=" in lower:
        return "JoinGame"

    return "Other"


def redact(line: str) -> str:
    for pattern, replacement in REDACT_PATTERNS:
        line = pattern.sub(replacement, line)
    return line


def parse_line(file_path: Path, line_no: int, raw: str) -> dict:
    redacted = redact(raw.rstrip())

    time_match = RE_LOG_TIME.search(raw)
    playlist_match = RE_PLAYLIST.search(raw)
    match_type_match = RE_MATCH_TYPE.search(raw)
    region_match = RE_REGION.search(raw)
    server_match = RE_SERVER.search(raw)

    playlist_id = None
    if playlist_match:
        playlist_id = playlist_match.group(1) or playlist_match.group(2)

    return {
        "file": file_path.name,
        "line_number": line_no,
        "log_time_prefix": time_match.group(0) if time_match else None,
        "event_type": classify_event(raw),
        "playlist_id": playlist_id,
        "match_type": match_type_match.group(1) if match_type_match else None,
        "region": region_match.group(1) if region_match else None,
        "server_name": server_match.group(1) if server_match else None,
        "raw_line_redacted": redacted,
    }


def resolve_logs_dir(cli_path: str | None) -> Path | None:
    if cli_path:
        path = Path(cli_path)
        return path if path.is_dir() else None

    env_path = os.environ.get("RLA_LOG_DIR", "").strip()
    if env_path:
        path = Path(env_path)
        return path if path.is_dir() else None

    for candidate in LOG_DIR_CANDIDATES:
        if candidate.is_dir():
            return candidate

    return None


def get_log_files(logs_dir: Path, limit_files: int) -> list[Path]:
    log_files = sorted(
        logs_dir.glob("*.log"),
        key=lambda file_path: file_path.stat().st_mtime,
        reverse=True,
    )

    if limit_files > 0:
        return log_files[:limit_files]

    return log_files


def scan(logs_dir: Path, limit_files: int) -> tuple[list[dict], int]:
    log_files = get_log_files(logs_dir, limit_files)
    events: list[dict] = []

    for log_file in log_files:
        try:
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            print(f"[probe] Could not read {log_file}: {exc}")
            continue

        for line_no, line in enumerate(lines, start=1):
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in TRIGGER_KEYWORDS):
                events.append(parse_line(log_file, line_no, line))

    return events, len(log_files)


def write_outputs(events: list[dict], logs_dir: Path, files_scanned: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "generated": generated,
        "logs_dir": str(logs_dir),
        "files_scanned": files_scanned,
        "events_found": len(events),
        "events": events,
    }

    OUTPUT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with OUTPUT_TXT.open("w", encoding="utf-8") as file:
        file.write("LAUNCH LOG JOIN EVENTS PROBE\n")
        file.write(f"generated    : {generated}\n")
        file.write(f"logs_dir     : {logs_dir}\n")
        file.write(f"files_scanned: {files_scanned}\n")
        file.write(f"events_found : {len(events)}\n")
        file.write("=" * 80 + "\n\n")

        for event in events:
            file.write(
                f"[{event['file']} L{event['line_number']}] "
                f"{event['event_type']} "
                f"playlist={event['playlist_id']} "
                f"match_type={event['match_type']}\n"
            )
            file.write(f"  {event['raw_line_redacted']}\n\n")


def count_field(events: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}

    for event in events:
        value = event.get(field)
        if value:
            counts[str(value)] = counts.get(str(value), 0) + 1

    return dict(sorted(counts.items(), key=lambda item: -item[1]))


def main() -> None:
    parser = argparse.ArgumentParser(description="RLA join events probe")
    parser.add_argument("--limit-files", type=int, default=0, help="Max log files to scan. 0 = all.")
    parser.add_argument("--logs-dir", type=str, default=None, help="Explicit path to Rocket League Logs folder.")
    args = parser.parse_args()

    logs_dir = resolve_logs_dir(args.logs_dir)
    if not logs_dir:
        print("[probe] Logs folder not found. Tried:")
        for candidate in LOG_DIR_CANDIDATES:
            print(f"  {candidate}")
        print("[probe] Set RLA_LOG_DIR env var or use --logs-dir <path>")
        sys.exit(1)

    events, files_scanned = scan(logs_dir, args.limit_files)
    write_outputs(events, logs_dir, files_scanned)

    playlist_counts = count_field(events, "playlist_id")
    match_type_counts = count_field(events, "match_type")

    print("LAUNCH LOG JOIN EVENTS PROBE")
    print(f"logs_dir     : {logs_dir}")
    print(f"files_scanned: {files_scanned}")
    print(f"events_found : {len(events)}")
    print(f"json_path    : {OUTPUT_JSON}")
    print(f"txt_path     : {OUTPUT_TXT}")
    print()

    print("playlist_counts:")
    for playlist_id, count in playlist_counts.items():
        print(f"  {playlist_id}: {count}")

    print("match_type_counts:")
    for match_type, count in match_type_counts.items():
        print(f"  {match_type}: {count}")

    print()

    for event in events[:30]:
        print(
            f"[{event['file']} L{event['line_number']}] "
            f"{event['event_type']} "
            f"playlist={event['playlist_id']} "
            f"match_type={event['match_type']}"
        )
        print(f"  {event['raw_line_redacted']}")


if __name__ == "__main__":
    main()