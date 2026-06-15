import React from "react";
import "./styles.css";
import { mockDashboardPayload } from "./mock/mockDashboardPayload";

const TABS = ["Overview", "Movement", "Boost", "Offence", "Defence"];

export default function App() {
  const payload       = mockDashboardPayload;
  const { system_status, session_summary, metric_cards, recent_matches } = payload;

  return (
    <div className="app-shell">

      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-title">
          {payload.app.name.split(" ").slice(0, 2).join(" ")}<br />
          {payload.app.name.split(" ").slice(2).join(" ")}
        </div>
        <div className="sidebar-mode">
          {session_summary.most_common_team_size
            ? `${session_summary.most_common_team_size}v${session_summary.most_common_team_size}`
            : "2v2"}
        </div>
        <div className={`status-pill ${system_status.state === "Ready" ? "ready" : "partial"}`}>
          ● {system_status.state}
        </div>
        <div className="sidebar-meta">
          {system_status.latest_display_map && (
            <span className="sidebar-item">Last: {system_status.latest_display_map}</span>
          )}
          <span className="sidebar-item">Loaded: {payload.summary.total_loaded}</span>
        </div>
        <button className="await-btn">Awaiting replay</button>
      </aside>

      {/* ── Main Panel ── */}
      <main className="main-panel">
        <h2 className="panel-heading">Today's Snapshot</h2>

        <div className="metric-grid">
          {metric_cards.map(card => (
            <div className={`metric-card tone-${card.tone}`} key={card.id}>
              <div className="metric-label">{card.label}</div>
              <div className="metric-value">{card.value}</div>
              <div className="metric-sub">{card.sublabel}</div>
            </div>
          ))}
        </div>

        <h3 className="section-heading">Last Games</h3>
        <div className="game-list">
          {recent_matches.map(m => (
            <div className="game-row" key={m.id}>
              <span className="game-map">{m.display_map_name}</span>
              <span className="game-type">{m.match_type ?? "—"}</span>
              <span className="game-score">{m.score_label}</span>
              <span className="game-secs">{m.seconds_label} min</span>
            </div>
          ))}
        </div>
      </main>

      {/* ── Details Panel ── */}
      <aside className="details-panel">
        <div className="tab-row">
          {TABS.map((t, i) => (
            <button className={`tab-button${i === 0 ? " active" : ""}`} key={t}>{t}</button>
          ))}
        </div>

        <h3 className="section-heading">Session Performance</h3>
        <div className="metric-card">
          <div className="metric-label">Session</div>
          <div className="metric-value">{session_summary.match_count} matches</div>
          <div className="metric-sub">{session_summary.total_minutes_label} min total</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Maps played</div>
          <div className="metric-value" style={{ fontSize: "13px", lineHeight: "1.6" }}>
            {session_summary.unique_display_maps.join(", ")}
          </div>
        </div>
        <div className="metric-card bridge-card">
          <div className="metric-label">Backend bridge</div>
          <div className="metric-value">Ready</div>
          <div className="metric-sub">get_dashboard_compact_payload()</div>
        </div>
      </aside>

    </div>
  );
}