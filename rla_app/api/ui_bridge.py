"""
RLA 2 — api/ui_bridge.py
Bridge limpio entre el motor Python y la futura UI.
Sin prints. Sin I/O directo. Sin servidor HTTP.
"""
from __future__ import annotations

from datetime import datetime

from rla_app.analysis.session_snapshot import build_session_snapshot
from rla_app.domain.map_names import get_display_map_name, normalize_map_name
from rla_app.storage.db_location import get_default_db_path
from rla_app.storage.match_reader import get_recent_matches

_APP_NAME    = "Rocket League Analyser"
_APP_VERSION = "0.1.0-dev"
_DATE_FMT    = "%Y-%m-%d %H-%M-%S"


# ── Helpers de ordenado / filtrado ────────────────────────────────────────────

def _date_sort_key(match_dict: dict) -> datetime:
    raw = match_dict.get("date")
    if raw:
        try:
            return datetime.strptime(raw.strip(), _DATE_FMT)
        except ValueError:
            pass
    return datetime.min


def _is_in_active_session(
    match_dict: dict,
    session_start: str | None,
    session_end: str | None,
) -> bool:
    if not session_start or not session_end:
        return False
    date = match_dict.get("date")
    return bool(date and session_start <= date <= session_end)


# ── Enriquecimiento de map fields ─────────────────────────────────────────────

def _enrich_match_map_fields(match_dict: dict) -> dict:
    d    = dict(match_dict)
    info = normalize_map_name(d.get("map_name"))
    d["display_map_name"] = info.display_name
    d["short_map_name"]   = info.short_name
    d["map_family"]       = info.family
    d["map_variant"]      = info.variant
    d["map_name_source"]  = info.source
    return d


# ── Session summary ───────────────────────────────────────────────────────────

def _build_session_summary(active: list[dict], snapshot_dict: dict) -> dict:
    first = active[0] if active else None
    most_played_display = (
        get_display_map_name(snapshot_dict.get("most_played_map"))
        if snapshot_dict.get("most_played_map") else None
    )
    return {
        "title":                       "Current Session",
        "match_count":                 len(active),
        "session_start":               snapshot_dict.get("session_start"),
        "session_end":                 snapshot_dict.get("session_end"),
        "total_minutes_label":         snapshot_dict.get("total_minutes_label", "0.0"),
        "average_match_minutes_label": snapshot_dict.get("average_match_minutes_label", "—"),
        "most_played_map":             snapshot_dict.get("most_played_map"),
        "most_played_display_map":     most_played_display,
        "most_common_team_size":       snapshot_dict.get("most_common_team_size"),
        "unique_maps":      sorted({m["map_name"]         for m in active if m.get("map_name")}),
        "unique_display_maps": sorted({m["display_map_name"] for m in active if m.get("display_map_name")}),
        "match_types":      sorted({m["match_type"]       for m in active if m.get("match_type")}),
        "team_sizes":       sorted({m["team_size"]        for m in active if m.get("team_size") is not None}),
        "latest_map":           first.get("map_name")         if first else None,
        "latest_display_map":   first.get("display_map_name") if first else None,
        "latest_match_type":    first.get("match_type")       if first else None,
        "latest_score_label":   first.get("score_label")      if first else None,
    }


# ── System status ─────────────────────────────────────────────────────────────

def _build_system_status(
    matches: list[dict],
    active: list[dict],
    summary: dict,
    snapshot_dict: dict,
) -> dict:
    total   = summary.get("total_loaded", 0)
    m_ready = summary.get("metadata_ready", 0)
    m_miss  = summary.get("metadata_missing", 0)
    first   = matches[0] if matches else None
    state   = ("Awaiting replay" if total == 0
               else "Ready" if m_miss == 0 else "Partial")
    msgs    = {"Awaiting replay": "Awaiting replay",
               "Ready": "Ready", "Partial": "Some replays need metadata"}
    return {
        "state": state, "has_matches": total > 0,
        "has_active_session":    len(active) > 0,
        "total_loaded":          total,
        "metadata_ready":        m_ready,
        "metadata_missing":      m_miss,
        "latest_match_date":     summary.get("latest_match_date"),
        "latest_map":            first.get("map_name")         if first else None,
        "latest_display_map":    first.get("display_map_name") if first else None,
        "latest_match_type":     first.get("match_type")       if first else None,
        "latest_parse_level":    first.get("parse_level")      if first else None,
        "latest_metadata_ready": first.get("metadata_ready", False) if first else False,
        "active_session_count":  len(active),
        "message": msgs[state],
    }


# ── Metric cards ──────────────────────────────────────────────────────────────

def _build_metric_cards(
    summary: dict,
    snapshot_dict: dict,
    session_summary: dict,
    system_status: dict,
) -> list[dict]:
    state    = system_status["state"]
    tone_map = {"Awaiting replay": "neutral", "Ready": "success", "Partial": "warning"}
    latest_map   = session_summary.get("latest_display_map") or session_summary.get("latest_map") or "—"
    latest_type  = session_summary.get("latest_match_type")  or "—"
    latest_score = session_summary.get("latest_score_label") or "—"
    return [
        {"id": "system_state",   "label": "System",
         "value": state,         "sublabel": system_status["message"],
         "tone": tone_map.get(state, "neutral")},
        {"id": "loaded_replays", "label": "Loaded Replays",
         "value": str(summary["total_loaded"]),
         "sublabel": f'{summary["metadata_ready"]} metadata ready', "tone": "neutral"},
        {"id": "active_session", "label": "Active Session",
         "value": str(session_summary["match_count"]),
         "sublabel": "matches in current session",                   "tone": "neutral"},
        {"id": "session_time",   "label": "Session Time",
         "value": f'{session_summary["total_minutes_label"]} min',
         "sublabel": "estimated replay time",                        "tone": "neutral"},
        {"id": "avg_match",      "label": "Avg Match",
         "value": f'{session_summary["average_match_minutes_label"]} min',
         "sublabel": "average duration",                             "tone": "neutral"},
        {"id": "latest_match",   "label": "Latest Match",
         "value": latest_map,
         "sublabel": f"{latest_type} · {latest_score}",             "tone": "neutral"},
    ]


# ── Payload completo ──────────────────────────────────────────────────────────

def get_dashboard_payload(limit: int = 20) -> dict:
    matches  = get_recent_matches(max(1, limit))
    snapshot = build_session_snapshot(max(1, limit))

    enriched     = [_enrich_match_map_fields(m.to_dict()) for m in matches]
    sorted_dicts = sorted(enriched, key=_date_sort_key, reverse=True)
    active_dicts = [d for d in sorted_dicts
                    if _is_in_active_session(d, snapshot.session_start, snapshot.session_end)]

    snapshot_dict   = snapshot.to_dict()
    session_summary = _build_session_summary(active_dicts, snapshot_dict)
    dates           = [m.date for m in matches if m.date]

    summary_dict = {
        "total_loaded":      len(matches),
        "metadata_ready":    sum(1 for m in matches if m.metadata_ready),
        "metadata_missing":  sum(1 for m in matches if not m.metadata_ready),
        "latest_match_date": max(dates) if dates else None,
    }

    system_status = _build_system_status(sorted_dicts, active_dicts, summary_dict, snapshot_dict)
    metric_cards  = _build_metric_cards(summary_dict, snapshot_dict, session_summary, system_status)

    return {
        "app":                    {"name": _APP_NAME, "version": _APP_VERSION},
        "database":               {"path": str(get_default_db_path())},
        "matches":                sorted_dicts,
        "active_session_matches": active_dicts,
        "summary":                summary_dict,
        "snapshot":               snapshot_dict,
        "session_summary":        session_summary,
        "system_status":          system_status,
        "metric_cards":           metric_cards,
    }


# ── Payload compacto ──────────────────────────────────────────────────────────

def get_dashboard_compact_payload(
    limit: int = 50,
    recent_limit: int = 10,
) -> dict:
    limit        = max(1, limit)
    recent_limit = max(0, recent_limit)

    full = get_dashboard_payload(limit)

    return {
        "app":                    full["app"],
        "database":               full["database"],
        "summary":                full["summary"],
        "snapshot":               full["snapshot"],
        "session_summary":        full["session_summary"],
        "system_status":          full["system_status"],
        "metric_cards":           full["metric_cards"],
        "active_session_matches": full["active_session_matches"],
        "recent_matches":         full["matches"][:recent_limit],
    }