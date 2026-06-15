"""
Dev diagnostic: scans Launch.log for MMR/rank/playlist candidate lines.
Usage:
    python -m rla_app.rank.launch_log_probe_dev
    python -m rla_app.rank.launch_log_probe_dev --tail 5000
    python -m rla_app.rank.launch_log_probe_dev --log "C:\\path\\Launch.log"
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

KEYWORDS = [
    "mmr", "skill", "skillrating", "skill rating", "playerSkill",
    "rank", "division", "tier", "playlist", "playlistid",
    "competitive", "ranked", "casual", "matchmaking",
    "gameresult", "onlinegame",
]

LOG_CANDIDATES = [
    Path.home() / "OneDrive" / "Documents" / "My Games" / "Rocket League" / "TAGame" / "Logs" / "Launch.log",
    Path.home() / "Documents" / "My Games" / "Rocket League" / "TAGame" / "Logs" / "Launch.log",
]

OUTPUT_DIR = Path.home() / "Documents" / "My Games" / "RLA" / "logs"
OUTPUT_FILE = OUTPUT_DIR / "launch_log_probe_matches.txt"


def resolve_log_path(cli_path: str | None) -> Path | None:
    if cli_path:
        p = Path(cli_path)
        return p if p.is_file() else None

    env = os.environ.get("RLA_LAUNCH_LOG", "").strip()
    if env:
        p = Path(env)
        return p if p.is_file() else None

    for candidate in LOG_CANDIDATES:
        if candidate.is_file():
            return candidate

    return None


def read_tail(log_path: Path, tail: int) -> list[str]:
    try:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return lines[-tail:] if tail < len(lines) else lines
    except OSError as e:
        print(f"[probe] Could not read file: {e}")
        return []


def find_candidates(lines: list[str]) -> list[tuple[int, str]]:
    results = []
    for i, line in enumerate(lines, start=1):
        low = line.lower()
        if any(kw.lower() in low for kw in KEYWORDS):
            results.append((i, line.rstrip()))
    return results


def write_report(log_path: Path, tail: int, candidates: list[tuple[int, str]]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"LAUNCH LOG PROBE REPORT\n")
        f.write(f"generated : {now}\n")
        f.write(f"log path  : {log_path}\n")
        f.write(f"tail lines: {tail}\n")
        f.write(f"keywords  : {', '.join(KEYWORDS)}\n")
        f.write(f"matches   : {len(candidates)}\n")
        f.write("=" * 80 + "\n\n")
        for line_no, text in candidates:
            f.write(f"[line {line_no:>6}] {text}\n")
    return OUTPUT_FILE


def main() -> None:
    parser = argparse.ArgumentParser(description="RLA Launch.log probe dev tool")
    parser.add_argument("--tail", type=int, default=5000, help="Number of lines to read from end of file")
    parser.add_argument("--log", type=str, default=None, help="Explicit path to Launch.log")
    args = parser.parse_args()

    log_path = resolve_log_path(args.log)

    if not log_path:
        print("[probe] Launch.log not found. Tried:")
        for c in LOG_CANDIDATES:
            print(f"  {c}")
        print("[probe] Set RLA_LAUNCH_LOG env var or use --log <path>")
        sys.exit(1)

    stat = log_path.stat()
    size_mb = stat.st_size / (1024 * 1024)
    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    lines = read_tail(log_path, args.tail)
    candidates = find_candidates(lines)
    report_path = write_report(log_path, args.tail, candidates)

    print("LAUNCH LOG PROBE")
    print(f"path           : {log_path}")
    print(f"size_mb        : {size_mb:.2f}")
    print(f"modified       : {modified}")
    print(f"tail_lines     : {len(lines)}")
    print(f"candidate_lines: {len(candidates)}")
    print(f"report_path    : {report_path}")
    print()

    for line_no, text in candidates:
        print(f"[{line_no:>6}] {text}")


if __name__ == "__main__":
    main()