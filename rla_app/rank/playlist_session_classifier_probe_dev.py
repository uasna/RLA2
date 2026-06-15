"""
Dev diagnostic: classifies join sessions by playlist (conservative candidates).
Input: launch_log_join_sessions_probe.json (from Fase 9A.2)
Usage:
    python -m rla_app.rank.playlist_session_classifier_probe_dev
    python -m rla_app.rank.playlist_session_classifier_probe_dev --input "C:\\path\\file.json"
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR     = Path.home() / "Documents" / "My Games" / "RLA" / "logs"
INPUT_FILE  = LOG_DIR / "launch_log_join_sessions_probe.json"
OUTPUT_JSON = LOG_DIR / "playlist_session_classifier_probe.json"
OUTPUT_TXT  = LOG_DIR / "playlist_session_classifier_probe.txt"

PLAYLIST_CATALOG: dict[str, dict] = {
    "2": {
        "label":      "Candidate Casual Doubles",
        "mode":       "2v2",
        "category":   "casual_candidate",
        "confidence": "medium",
    },
    "3": {
        "label":      "Candidate Casual Standard",
        "mode":       "3v3",
        "category":   "casual_candidate",
        "confidence": "medium",
    },
    "11": {
        "label":      "Candidate Ranked Doubles",
        "mode":       "2v2",
        "category":   "ranked_candidate",
        "confidence": "medium",
    },
}


def load_sessions(input_path: Path) -> list[dict]:
    if not input_path.is_file():
        print(f"[probe] Input file not found: {input_path}")
        sys.exit(1)
    try:
        data = json.loads(input_path.read_text(encoding="utf-8", errors="replace"))
        return data.get("sessions", [])
    except Exception as e:
        print(f"[probe] Failed to read input: {e}")
        sys.exit(1)


def classify_session(session: dict) -> dict:
    pid = str(session.get("playlist_id") or "")
    catalog = PLAYLIST_CATALOG.get(pid)

    if catalog:
        label      = catalog["label"]
        mode       = catalog["mode"]
        category   = catalog["category"]
        confidence = catalog["confidence"]
    else:
        label      = f"Unknown Playlist {pid}" if pid else "Unknown Playlist"
        mode       = "unknown"
        category   = "unknown"
        confidence = "low"

    event_types         = session.get("event_types") or []
    has_ranked_reconnect = "RankedReconnect" in event_types

    if has_ranked_reconnect:
        ranked_signal = "strong"
    elif category.startswith("ranked"):
        ranked_signal = "catalog_candidate"
    else:
        ranked_signal = "none"

    return {
        "server_name":           session.get("server_name"),
        "playlist_id":           pid or None,
        "region":                session.get("region"),
        "mode":                  mode,
        "label":                 label,
        "category":              category,
        "confidence":            confidence,
        "has_ranked_reconnect":  has_ranked_reconnect,
        "ranked_signal":         ranked_signal,
        "event_count":           session.get("event_count"),
        "first_file":            session.get("first_file"),
        "first_line":            session.get("first_line"),
        "last_file":             session.get("last_file"),
        "last_line":             session.get("last_line"),
    }


def count_field(sessions: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for s in sessions:
        val = str(s.get(field) or "")
        if val:
            counts[val] = counts.get(val, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def write_outputs(classified: list[dict], input_path: Path) -> tuple[dict, dict, dict]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    category_counts      = count_field(classified, "category")
    playlist_counts      = count_field(classified, "playlist_id")
    ranked_signal_counts = count_field(classified, "ranked_signal")

    payload = {
        "generated":           now,
        "input_path":          str(input_path),
        "sessions_classified": len(classified),
        "category_counts":     category_counts,
        "playlist_counts":     playlist_counts,
        "ranked_signal_counts": ranked_signal_counts,
        "classified_sessions": classified,
    }
    OUTPUT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("PLAYLIST SESSION CLASSIFIER PROBE\n")
        f.write(f"generated           : {now}\n")
        f.write(f"input_path          : {input_path}\n")
        f.write(f"sessions_classified : {len(classified)}\n")
        f.write("=" * 80 + "\n\n")
        for s in classified:
            f.write(
                f"playlist={s['playlist_id']} mode={s['mode']} "
                f"category={s['category']} confidence={s['confidence']} "
                f"signal={s['ranked_signal']} server={s['server_name']}\n"
            )

    return category_counts, playlist_counts, ranked_signal_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="RLA playlist session classifier probe")
    parser.add_argument("--input", type=str, default=None)
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else INPUT_FILE
    sessions   = load_sessions(input_path)
    classified = [classify_session(s) for s in sessions]

    category_counts, playlist_counts, ranked_signal_counts = write_outputs(classified, input_path)

    print("PLAYLIST SESSION CLASSIFIER PROBE")
    print(f"input_path          : {input_path}")
    print(f"sessions_classified : {len(classified)}")
    print(f"json_path           : {OUTPUT_JSON}")
    print(f"txt_path            : {OUTPUT_TXT}")
    print()
    print("category_counts:")
    for k, v in category_counts.items():
        print(f"  {k}: {v}")
    print("playlist_counts:")
    for k, v in playlist_counts.items():
        print(f"  {k}: {v}")
    print("ranked_signal_counts:")
    for k, v in ranked_signal_counts.items():
        print(f"  {k}: {v}")
    print()

    for s in classified[:30]:
        print(
            f"playlist={s['playlist_id']} mode={s['mode']} "
            f"category={s['category']} signal={s['ranked_signal']} "
            f"server={s['server_name']}"
        )


if __name__ == "__main__":
    main()