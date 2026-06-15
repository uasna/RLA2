"""
Dev diagnostic: matches parsed replays with classified Launch.log playlist sessions.
Safe to persist: NEVER (diagnostic only).
Usage:
    python -m rla_app.rank.replay_playlist_matcher_probe_dev
    python -m rla_app.rank.replay_playlist_matcher_probe_dev --sessions "C:\\path\\file.json"
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR        = Path.home() / "Documents" / "My Games" / "RLA" / "logs"
DEFAULT_SESSIONS = LOG_DIR / "playlist_session_classifier_probe.json"
OUTPUT_JSON    = LOG_DIR / "replay_playlist_matcher_probe.json"
OUTPUT_TXT     = LOG_DIR / "replay_playlist_matcher_probe.txt"

SAFE_MATCH_KEYS = [
    "id", "match_id", "replay_id", "file_name", "replay_name",
    "map_name", "mode", "team_size", "score_label", "duration_label",
    "total_seconds_played", "created_at", "indexed_at", "parsed_at",
    "modified_at", "mtime",
]


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_classified_sessions(path: Path) -> list[dict]:
    if not path.is_file():
        print(f"[probe] Sessions file not found: {path}")
        sys.exit(1)
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data.get("classified_sessions", [])
    except Exception as e:
        print(f"[probe] Failed to read sessions: {e}")
        sys.exit(1)


def load_matches_from_payload() -> tuple[list[dict], str]:
    try:
        from rla_app.api.ui_bridge import get_dashboard_compact_payload
        payload = get_dashboard_compact_payload(limit=100, recent_limit=100)
    except Exception as e:
        print(f"[probe] Could not load payload: {e}")
        return [], "error"

    recent  = payload.get("recent_matches") or []
    active  = payload.get("active_session_matches") or []

    if recent and active:
        seen, combined = set(), []
        for m in recent + active:
            key = m.get("id") or m.get("replay_id") or m.get("file_name")
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            combined.append(m)
        return combined, "recent_matches+active_session_matches"

    if recent:
        return recent, "recent_matches"
    if active:
        return active, "active_session_matches"
    return [], "empty"


# ── Normalizers ───────────────────────────────────────────────────────────────

def normalize_match(index: int, match: dict) -> dict:
    raw_mode = match.get("mode") or match.get("team_mode") or match.get("game_mode")
    return {
        "match_index":          index,
        "available_keys":       list(match.keys()),
        "id":                   match.get("id"),
        "match_id":             match.get("match_id"),
        "replay_id":            match.get("replay_id"),
        "file_name":            match.get("file_name"),
        "replay_name":          match.get("replay_name"),
        "map_name":             match.get("map_name"),
        "mode":                 match.get("mode"),
        "team_size":            match.get("team_size"),
        "score_label":          match.get("score_label"),
        "duration_label":       match.get("duration_label"),
        "total_seconds_played": match.get("total_seconds_played"),
        "created_at":           match.get("created_at"),
        "indexed_at":           match.get("indexed_at"),
        "parsed_at":            match.get("parsed_at"),
        "modified_at":          match.get("modified_at"),
        "mtime":                match.get("mtime"),
        "raw_mode_candidate":   raw_mode,
    }


def normalize_classified_session(index: int, session: dict) -> dict:
    return {
        "session_index":        index,
        "server_name":          session.get("server_name"),
        "playlist_id":          session.get("playlist_id"),
        "region":               session.get("region"),
        "mode":                 session.get("mode"),
        "label":                session.get("label"),
        "category":             session.get("category"),
        "confidence":           session.get("confidence"),
        "has_ranked_reconnect": session.get("has_ranked_reconnect"),
        "ranked_signal":        session.get("ranked_signal"),
        "event_count":          session.get("event_count"),
        "first_file":           session.get("first_file"),
        "first_line":           session.get("first_line"),
        "last_file":            session.get("last_file"),
        "last_line":            session.get("last_line"),
    }


# ── Mode conversion ───────────────────────────────────────────────────────────

def team_size_to_mode(team_size) -> str:
    try:
        ts = int(team_size)
        return {1: "1v1", 2: "2v2", 3: "3v3"}.get(ts, "unknown")
    except (TypeError, ValueError):
        return "unknown"


# ── Matcher ───────────────────────────────────────────────────────────────────

def build_candidate_pairs(
    norm_matches: list[dict],
    norm_sessions: list[dict],
) -> list[dict]:
    # Sort sessions by file + line
    sorted_sessions = sorted(
        norm_sessions,
        key=lambda s: (s.get("first_file") or "", s.get("first_line") or 0),
    )

    used_sessions: set[int] = set()
    pairs: list[dict] = []

    for m in norm_matches:
        expected_mode = team_size_to_mode(m.get("team_size"))

        matched_session = None
        for s in sorted_sessions:
            if s["session_index"] in used_sessions:
                continue
            s_mode = s.get("mode") or "unknown"
            if expected_mode == "unknown" or s_mode == expected_mode or s_mode == "unknown":
                matched_session = s
                break

        if matched_session is None:
            continue

        used_sessions.add(matched_session["session_index"])
        pairs.append({
            "pair_index":            len(pairs),
            "match_index":           m["match_index"],
            "session_index":         matched_session["session_index"],
            "match_map_name":        m.get("map_name"),
            "match_team_size":       m.get("team_size"),
            "match_expected_mode":   expected_mode,
            "match_score_label":     m.get("score_label"),
            "match_duration_label":  m.get("duration_label"),
            "session_playlist_id":   matched_session.get("playlist_id"),
            "session_mode":          matched_session.get("mode"),
            "session_category":      matched_session.get("category"),
            "session_ranked_signal": matched_session.get("ranked_signal"),
            "session_server_name":   matched_session.get("server_name"),
            "match_confidence":      "diagnostic_order_only",
            "safe_to_persist":       False,
        })

    return pairs


# ── Counters ─────────────────────────────────────────────────────────────────

def count_field(items: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        val = str(item.get(field) or "")
        if val:
            counts[val] = counts.get(val, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


# ── Output ────────────────────────────────────────────────────────────────────

def write_outputs(
    sessions_path: Path,
    matches_source: str,
    norm_matches: list[dict],
    norm_sessions: list[dict],
    pairs: list[dict],
) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    match_key_samples = {
        f"match_{i}": m.get("available_keys", [])
        for i, m in enumerate(norm_matches[:5])
    }

    session_category_counts = count_field(norm_sessions, "category")
    session_playlist_counts = count_field(norm_sessions, "playlist_id")

    payload = {
        "generated":                  now,
        "sessions_input_path":        str(sessions_path),
        "matches_source":             matches_source,
        "matches_found":              len(norm_matches),
        "sessions_found":             len(norm_sessions),
        "candidate_pairs_found":      len(pairs),
        "match_key_samples":          match_key_samples,
        "session_category_counts":    session_category_counts,
        "session_playlist_counts":    session_playlist_counts,
        "candidate_pairs":            pairs,
        "normalized_matches_preview": norm_matches[:10],
        "normalized_sessions_preview": norm_sessions[:10],
        "notes": [
            "match_confidence=diagnostic_order_only: pairs are positional, not verified.",
            "safe_to_persist=false: do NOT write these to DB.",
            "Matching is conservative by team_size->mode only.",
        ],
    }
    OUTPUT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("REPLAY PLAYLIST MATCHER PROBE\n")
        f.write(f"generated           : {now}\n")
        f.write(f"sessions_input_path : {sessions_path}\n")
        f.write(f"matches_source      : {matches_source}\n")
        f.write(f"matches_found       : {len(norm_matches)}\n")
        f.write(f"sessions_found      : {len(norm_sessions)}\n")
        f.write(f"candidate_pairs     : {len(pairs)}\n")
        f.write("=" * 80 + "\n\n")
        for p in pairs:
            f.write(
                f"pair#{p['pair_index']} "
                f"match#{p['match_index']} map={p['match_map_name']} "
                f"team_size={p['match_team_size']} expected={p['match_expected_mode']} "
                f"-> playlist={p['session_playlist_id']} "
                f"category={p['session_category']} "
                f"signal={p['session_ranked_signal']} "
                f"confidence={p['match_confidence']}\n"
            )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="RLA replay playlist matcher probe")
    parser.add_argument("--sessions", type=str, default=None)
    args = parser.parse_args()

    sessions_path = Path(args.sessions) if args.sessions else DEFAULT_SESSIONS

    raw_sessions = load_classified_sessions(sessions_path)
    raw_matches, matches_source = load_matches_from_payload()

    norm_sessions = [normalize_classified_session(i, s) for i, s in enumerate(raw_sessions)]
    norm_matches  = [normalize_match(i, m) for i, m in enumerate(raw_matches)]
    pairs         = build_candidate_pairs(norm_matches, norm_sessions)

    write_outputs(sessions_path, matches_source, norm_matches, norm_sessions, pairs)

    session_category_counts = count_field(norm_sessions, "category")
    session_playlist_counts = count_field(norm_sessions, "playlist_id")

    print("REPLAY PLAYLIST MATCHER PROBE")
    print(f"sessions_input_path  : {sessions_path}")
    print(f"matches_source       : {matches_source}")
    print(f"matches_found        : {len(norm_matches)}")
    print(f"sessions_found       : {len(norm_sessions)}")
    print(f"candidate_pairs_found: {len(pairs)}")
    print(f"json_path            : {OUTPUT_JSON}")
    print(f"txt_path             : {OUTPUT_TXT}")
    print()
    print("session_category_counts:")
    for k, v in session_category_counts.items():
        print(f"  {k}: {v}")
    print("session_playlist_counts:")
    for k, v in session_playlist_counts.items():
        print(f"  {k}: {v}")
    print()
    print("match_key_samples:")
    for i, m in enumerate(norm_matches[:5]):
        print(f"  match {i} keys: {m.get('available_keys', [])}")
    print()
    print("candidate pairs preview:")
    for p in pairs[:30]:
        print(
            f"  match#{p['match_index']} "
            f"map={p['match_map_name']} "
            f"team_size={p['match_team_size']} "
            f"expected={p['match_expected_mode']} "
            f"-> playlist={p['session_playlist_id']} "
            f"category={p['session_category']} "
            f"signal={p['session_ranked_signal']} "
            f"confidence={p['match_confidence']}"
        )


if __name__ == "__main__":
    main()