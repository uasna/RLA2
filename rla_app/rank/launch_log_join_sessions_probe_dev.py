"""
Dev diagnostic: groups launch log join events into match sessions by server_name.
Input: launch_log_join_events_probe.json (from Fase 9A.1)
Usage:
    python -m rla_app.rank.launch_log_join_sessions_probe_dev
    python -m rla_app.rank.launch_log_join_sessions_probe_dev --input "C:\\path\\events.json"
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LOG_DIR     = Path.home() / "Documents" / "My Games" / "RLA" / "logs"
INPUT_FILE  = LOG_DIR / "launch_log_join_events_probe.json"
OUTPUT_JSON = LOG_DIR / "launch_log_join_sessions_probe.json"
OUTPUT_TXT  = LOG_DIR / "launch_log_join_sessions_probe.txt"


def load_events(input_path: Path) -> list[dict]:
    if not input_path.is_file():
        print(f"[probe] Input file not found: {input_path}")
        sys.exit(1)
    try:
        data = json.loads(input_path.read_text(encoding="utf-8", errors="replace"))
        return data.get("events", [])
    except Exception as e:
        print(f"[probe] Failed to read input: {e}")
        sys.exit(1)


def first_non_null(items: list, key: str):
    return next((ev[key] for ev in items if ev.get(key)), None)


def unique_ordered(items: list, key: str) -> list:
    seen, result = set(), []
    for ev in items:
        val = ev.get(key)
        if val and val not in seen:
            seen.add(val)
            result.append(val)
    return result


def build_sessions(events: list[dict]) -> list[dict]:
    # Group by server_name; skip events with no server_name
    buckets: dict[str, list[dict]] = defaultdict(list)
    for ev in events:
        sn = ev.get("server_name")
        if sn:
            buckets[sn].append(ev)

    sessions = []
    for server_name, evs in buckets.items():
        session = {
            "server_name":           server_name,
            "playlist_id":           first_non_null(evs, "playlist_id"),
            "region":                first_non_null(evs, "region"),
            "first_file":            evs[0].get("file"),
            "first_line":            evs[0].get("line_number"),
            "last_file":             evs[-1].get("file"),
            "last_line":             evs[-1].get("line_number"),
            "first_log_time_prefix": evs[0].get("log_time_prefix"),
            "last_log_time_prefix":  evs[-1].get("log_time_prefix"),
            "event_types":           unique_ordered(evs, "event_type"),
            "event_count":           len(evs),
            "raw_events":            [ev.get("raw_line_redacted", "") for ev in evs[:10]],
        }
        sessions.append(session)

    # Sort by first file + first line for readability
    sessions.sort(key=lambda s: (s["first_file"] or "", s["first_line"] or 0))
    return sessions


def count_field(sessions: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for s in sessions:
        val = s.get(field)
        if val:
            counts[str(val)] = counts.get(str(val), 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def write_outputs(sessions: list[dict], input_path: Path) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    playlist_counts = count_field(sessions, "playlist_id")
    region_counts   = count_field(sessions, "region")

    payload = {
        "generated":       now,
        "input_path":      str(input_path),
        "sessions_found":  len(sessions),
        "playlist_counts": playlist_counts,
        "region_counts":   region_counts,
        "sessions":        sessions,
    }
    OUTPUT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("LAUNCH LOG JOIN SESSIONS PROBE\n")
        f.write(f"generated     : {now}\n")
        f.write(f"input_path    : {input_path}\n")
        f.write(f"sessions_found: {len(sessions)}\n")
        f.write("=" * 80 + "\n\n")
        for s in sessions:
            f.write(f"server={s['server_name']}\n")
            f.write(f"  playlist={s['playlist_id']}  region={s['region']}"
                    f"  events={s['event_count']}\n")
            f.write(f"  first=[{s['first_file']} L{s['first_line']}]"
                    f"  last=[{s['last_file']} L{s['last_line']}]\n")
            f.write(f"  event_types={s['event_types']}\n")
            for raw in s["raw_events"]:
                f.write(f"    {raw}\n")
            f.write("\n")

    return playlist_counts, region_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="RLA join sessions probe")
    parser.add_argument("--input", type=str, default=None,
                        help="Path to launch_log_join_events_probe.json")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else INPUT_FILE

    events   = load_events(input_path)
    sessions = build_sessions(events)
    playlist_counts, region_counts = write_outputs(sessions, input_path)

    print("LAUNCH LOG JOIN SESSIONS PROBE")
    print(f"input_path    : {input_path}")
    print(f"sessions_found: {len(sessions)}")
    print(f"json_path     : {OUTPUT_JSON}")
    print(f"txt_path      : {OUTPUT_TXT}")
    print()
    print("playlist_counts:")
    for k, v in playlist_counts.items():
        print(f"  {k}: {v}")
    print("region_counts:")
    for k, v in region_counts.items():
        print(f"  {k}: {v}")
    print()

    for s in sessions[:30]:
        print(f"server={s['server_name']}")
        print(f"  playlist={s['playlist_id']}  region={s['region']}"
              f"  events={s['event_count']}")
        print(f"  first=[{s['first_file']} L{s['first_line']}]"
              f"  last=[{s['last_file']} L{s['last_line']}]")


if __name__ == "__main__":
    main()