import React from "react";
import type { DashboardCompactPayload } from "../types/dashboardPayload";
import type { DashboardDataSource } from "../services/dashboardData";

function formatTime(d: Date): string {
  return d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

interface SidebarProps {
  payload: DashboardCompactPayload;
  dataSource: DashboardDataSource;
  isRefreshing: boolean;
  lastLoadedAt: Date | null;
  onRefresh: () => void;
  autoRefreshEnabled: boolean;
  autoRefreshIntervalSeconds: number;
  autoRefreshAvailable: boolean;
  onToggleAutoRefresh: () => void;
}

export default function Sidebar({
  payload,
  dataSource,
  isRefreshing,
  lastLoadedAt,
  onRefresh,
  autoRefreshEnabled,
  autoRefreshIntervalSeconds,
  autoRefreshAvailable,
  onToggleAutoRefresh,
}: SidebarProps) {
  const { system_status, session_summary, summary } = payload;
  const statusClass = system_status.state === "Ready" ? "ready" : "partial";

  const autoRefreshActive = autoRefreshEnabled && autoRefreshAvailable;

  return (
    <aside className="sidebar">
      <div className="sidebar-title">
        Rocket League<br />Analyser
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
        <span className="sidebar-item">Loaded: {summary.total_loaded}</span>
        <span className={`sidebar-item source-badge source-badge--${dataSource}`}>
          Data source: {dataSource}
        </span>
        <span className="sidebar-item sidebar-item--mono">
          Last load: {lastLoadedAt ? formatTime(lastLoadedAt) : "—"}
        </span>
      </div>

      <button
        className="await-btn"
        onClick={onRefresh}
        disabled={isRefreshing}
        aria-label="Refresh payload from backend"
      >
        {isRefreshing ? "Refreshing..." : "⟳ Refresh Payload"}
      </button>

      {/* ── Auto-refresh block ── */}
      <div className="auto-refresh-box">
        <div className="auto-refresh-line">
          <span className="auto-refresh-status">
            Auto refresh:{" "}
            <strong className={autoRefreshActive ? "ar-on" : "ar-off"}>
              {autoRefreshActive ? "On" : "Off"}
            </strong>
          </span>
        </div>
        <div className="auto-refresh-line auto-refresh-hint">
          Every {autoRefreshIntervalSeconds}s · API only
          {!autoRefreshAvailable && (
            <span className="ar-paused"> · paused</span>
          )}
        </div>
        <button
          className="auto-refresh-button"
          onClick={onToggleAutoRefresh}
          disabled={!autoRefreshAvailable}
          aria-label={autoRefreshEnabled ? "Disable auto refresh" : "Enable auto refresh"}
        >
          {autoRefreshEnabled ? "Auto Refresh Off" : "Auto Refresh On"}
        </button>
      </div>
    </aside>
  );
}