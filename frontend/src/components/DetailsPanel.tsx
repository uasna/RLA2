import React from "react";
import type { SessionSummary } from "../types/dashboardPayload";
import type { DashboardDataSource } from "../services/dashboardData";

const TABS = ["Overview", "Movement", "Boost", "Offence", "Defence"];

interface DetailsPanelProps {
  sessionSummary: SessionSummary;
  dataSource: DashboardDataSource;
}

function bridgeLabel(source: DashboardDataSource): string {
  if (source === "api")  return "Connected";
  if (source === "json") return "Static JSON";
  return "Ready";
}

function bridgeSub(source: DashboardDataSource): string {
  if (source === "api")  return "Loaded from local backend API";
  if (source === "json") return "Loaded from dashboard_payload.json";
  return "Using mock — start API or export payload";
}

export default function DetailsPanel({
  sessionSummary,
  dataSource,
}: DetailsPanelProps) {
  return (
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
        <div className="metric-value">{sessionSummary.match_count} matches</div>
        <div className="metric-sub">
          {sessionSummary.total_minutes_label} min total
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Avg duration</div>
        <div className="metric-value">
          {sessionSummary.average_match_minutes_label} min
        </div>
        <div className="metric-sub">per match</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Maps played</div>
        <div
          className="metric-value"
          style={{ fontSize: "13px", lineHeight: "1.6" }}
        >
          {sessionSummary.unique_display_maps.join(", ") || "—"}
        </div>
      </div>

      <div className="metric-card bridge-card">
        <div className="metric-label">Backend bridge</div>
        <div className="metric-value">{bridgeLabel(dataSource)}</div>
        <div className="metric-sub">{bridgeSub(dataSource)}</div>
      </div>
    </aside>
  );
}