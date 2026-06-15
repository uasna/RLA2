// Auto-aligned with docs/ui_payload_contract.md and rla_app.api.ui_bridge compact payload.
// Do not calculate W/L from score_label yet. Team assignment is not available.

export type CardTone = "neutral" | "success" | "warning";
export type SystemState = "Ready" | "Partial" | "Awaiting replay";
export type MapNameSource = "known" | "fallback" | "missing";

export interface AppInfo {
  name: string;
  version: string;
}

export interface DatabaseInfo {
  path: string;
}

export interface DashboardSummary {
  total_loaded: number;
  metadata_ready: number;
  metadata_missing: number;
  latest_match_date: string | null;
}

export interface SessionSnapshot {
  loaded_matches: number;
  total_matches: number;
  metadata_ready: number;
  metadata_missing: number;
  latest_day: string | null;
  matches_on_latest_day: number;
  online_matches: number;
  private_matches: number;
  other_match_types: number;
  most_played_map: string | null;
  most_common_team_size: number | null;
  total_seconds: number;
  total_minutes_label: string;
  average_match_seconds: number | null;
  average_match_minutes_label: string;
  session_start: string | null;
  session_end: string | null;
  session_gap_hours: number;
}

export interface SessionSummary {
  title: string;
  match_count: number;
  session_start: string | null;
  session_end: string | null;
  total_minutes_label: string;
  average_match_minutes_label: string;
  most_played_map: string | null;
  most_played_display_map: string | null;
  most_common_team_size: number | null;
  unique_maps: string[];
  unique_display_maps: string[];
  match_types: string[];
  team_sizes: number[];
  latest_map: string | null;
  latest_display_map: string | null;
  latest_match_type: string | null;
  latest_score_label: string | null;
}

export interface SystemStatus {
  state: SystemState;
  message: string;
  has_matches: boolean;
  has_active_session: boolean;
  total_loaded: number;
  metadata_ready: number;
  metadata_missing: number;
  latest_match_date: string | null;
  latest_map: string | null;
  latest_display_map: string | null;
  latest_match_type: string | null;
  latest_parse_level: string | null;
  latest_metadata_ready: boolean;
  active_session_count: number;
}

export interface MetricCard {
  id: string;
  label: string;
  value: string;
  sublabel: string;
  tone: CardTone;
}

export interface MatchItem {
  id: number;
  file_name: string;
  status: string | null;
  parse_status: string | null;
  parse_level: string | null;
  meta_status: string | null;
  date: string | null;
  map_name: string | null;
  match_type: string | null;
  team_size: number | null;
  team0_score: number | null;
  team1_score: number | null;
  total_seconds_played: number | null;
  replay_name: string | null;
  score_label: string;
  seconds_label: string;
  metadata_ready: boolean;
  display_map_name: string;
  short_map_name: string;
  map_family: string | null;
  map_variant: string | null;
  map_name_source: MapNameSource;
}

export interface DashboardCompactPayload {
  app: AppInfo;
  database: DatabaseInfo;
  summary: DashboardSummary;
  snapshot: SessionSnapshot;
  session_summary: SessionSummary;
  system_status: SystemStatus;
  metric_cards: MetricCard[];
  active_session_matches: MatchItem[];
  recent_matches: MatchItem[];
}