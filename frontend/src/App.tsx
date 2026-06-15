import React from "react";
import "./styles.css";
import type { DashboardCompactPayload } from "./types/dashboardPayload";
import { mockDashboardPayload } from "./mock/mockDashboardPayload";
import { loadDashboardPayload } from "./services/dashboardData";

const TABS = ["Overview", "Movement", "Boost", "Offence", "Defence"];

function formatTime(d: Date): string {
  return d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function App() {
  const [payload, setPayload] =
    React.useState<DashboardCompactPayload>(mockDashboardPayload);
  const [dataSource, setDataSource] = React.useState<"mock" | "json">("mock");
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [lastLoadedAt, setLastLoadedAt] = React.useState<Date | null>(null);

  const refreshPayload = React.useCallback(async () => {
    setIsRefreshing(true);
    try {
      // Attempt to fetch the real JSON directly so we can detect the source
      // without modifying dashboardData.ts.
      let loaded: DashboardCompactPayload;
      let source: "mock" | "json" = "mock";

      try {
        const res = await fetch("/dashboard_payload.json", {
          cache: "no-store",
        });
        if (res.ok) {
          loaded = (await res.json()) as DashboardCompactPayload;
          source = "json";
        } else {
          loaded = await loadDashboardPayload(); // returns mock as fallback
        }
      } catch {
        loaded = await loadDashboardPayload(); // returns mock as fallback
      }

      setPayload(loaded);
      setDataSource(source);
      setLastLoadedAt(new Date());
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  React.useEffect(() => {
    void refreshPayload();
  }, [refreshPayload]);

  const { system_status, session_summary, metric_cards, recent_matches } =
    payload;
  const statusClass =
    system_status.state === "Ready" ? "ready" : "partial";

  return (
    <div className="app-shell">
      {/* ── SIDEBAR ── */}
      <aside className="sidebar">
        <div className="sidebar-title">
          Rocket League
          <br />
          Analyser
        </div>

        <div className="sidebar-mode">
          {session_summary.most_common_team_size
            ? `${session_summary.most_common_team_size}v${session_summary.most_common_team_size}`
            : "2v2"}
        </div>

        <div className={`status-pill ${statusClass}`}>
          ● {system_status.state}
        </div>

        <div className="sidebar-meta">
          {system_status.latest_display_map && (
            <span className="sidebar-item">
              Last: {system_status.latest_display_map}
            </span>
          )}
          <span className="sidebar-item">
            Loaded: {payload.summary.total_loaded}
          </span>
          <span className={`sidebar-item source-badge source-badge--${dataSource}`}>
            Data source: {dataSource}
          </span>
          <span className="sidebar-item sidebar-item--mono">
            Last load: {lastLoadedAt ? formatTime(lastLoadedAt) : "—"}
          </span>
        </div>

        <button
          className="await-btn"
          onClick={refreshPayload}
          disabled={isRefreshing}
          aria-label="Refresh payload from backend"
        >
          {isRefreshing ? "Refreshing…" : "⟳ Refresh Payload"}
        </button>
      </aside>

      {/* ── MAIN PANEL ── */}
      <main className="main-panel">
        <h2 className="panel-heading">Today's Snapshot</h2>

        <div className="metric-grid">
          {metric_cards.map((card) => (
            <div className={`metric-card tone-${card.tone}`} key={card.id}>
              <div className="metric-label">{card.label}</div>
              <div className="metric-value">{card.value}</div>
              <div className="metric-sub">{card.sublabel}</div>
            </div>
          ))}
        </div>

        <h3 className="section-heading">Last Games</h3>

        <div className="game-list">
          {recent_matches.map((match) => (
            <div className="game-row" key={match.id}>
              <span className="game-map">{match.display_map_name}</span>
              <span className="game-type">{match.match_type ?? "—"}</span>
              <span className="game-score">{match.score_label}</span>
              <span className="game-secs">{match.seconds_label} min</span>
            </div>
          ))}
        </div>
      </main>

      {/* ── DETAILS PANEL ── */}
      <aside className="details-panel">
        <div className="tab-row">
          {TABS.map((tab, index) => (
            <button
              className={`tab-button${index === 0 ? " active" : ""}`}
              key={tab}
            >
              {tab}
            </button>
          ))}
        </div>

        <h3 className="section-heading">Session Performance</h3>

        <div className="metric-card">
          <div className="metric-label">Session</div>
          <div className="metric-value">
            {session_summary.match_count} matches
          </div>
          <div className="metric-sub">
            {session_summary.total_minutes_label} min total
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Avg duration</div>
          <div className="metric-value">
            {session_summary.average_match_minutes_label} min
          </div>
          <div className="metric-sub">per match</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Maps played</div>
          <div
            className="metric-value"
            style={{ fontSize: "13px", lineHeight: "1.6" }}
          >
            {session_summary.unique_display_maps.join(", ") || "—"}
          </div>
        </div>

        <div className="metric-card bridge-card">
          <div className="metric-label">Backend bridge</div>
          <div className="metric-value">
            {dataSource === "json" ? "Connected" : "Ready"}
          </div>
          <div className="metric-sub">
            {dataSource === "json"
              ? "Loaded from dashboard_payload.json"
              : "Using mock — export payload to load real data"}
          </div>
        </div>
      </aside>
    </div>
  );
}