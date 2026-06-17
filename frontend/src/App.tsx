import React from "react";
import "./styles.css";
import type { DashboardCompactPayload } from "./types/dashboardPayload";
import type { DashboardDataSource } from "./services/dashboardData";
import { mockDashboardPayload } from "./mock/mockDashboardPayload";
import { loadDashboardPayloadWithSource } from "./services/dashboardData";
import Sidebar from "./components/Sidebar";
import MetricGrid from "./components/MetricGrid";
import GameList from "./components/GameList";
import DetailsPanel from "./components/DetailsPanel";

const AUTO_REFRESH_INTERVAL_MS = 10_000;

export default function App() {
  const [payload, setPayload] =
    React.useState<DashboardCompactPayload>(mockDashboardPayload);
  const [dataSource, setDataSource] = React.useState<DashboardDataSource>("mock");
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [lastLoadedAt, setLastLoadedAt] = React.useState<Date | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = React.useState(true);

  // Keep a ref so the interval callback always sees the latest values
  // without being recreated on every render.
  const isRefreshingRef = React.useRef(false);
  const dataSourceRef   = React.useRef<DashboardDataSource>("mock");

  const refreshPayload = React.useCallback(async () => {
    if (isRefreshingRef.current) return;          // skip if already in flight
    isRefreshingRef.current = true;
    setIsRefreshing(true);
    try {
      const { payload: loaded, source } = await loadDashboardPayloadWithSource();
      setPayload(loaded);
      setDataSource(source);
      dataSourceRef.current = source;
      setLastLoadedAt(new Date());
    } finally {
      isRefreshingRef.current = false;
      setIsRefreshing(false);
    }
  }, []);

  // Initial load
  React.useEffect(() => {
    void refreshPayload();
  }, [refreshPayload]);

  // Auto-refresh: only when enabled AND current source is "api"
  React.useEffect(() => {
    if (!autoRefreshEnabled) return;

    const id = setInterval(() => {
      if (dataSourceRef.current === "api") {
        void refreshPayload();
      }
    }, AUTO_REFRESH_INTERVAL_MS);

    return () => clearInterval(id);
  }, [autoRefreshEnabled, refreshPayload]);

  const handleToggleAutoRefresh = React.useCallback(() => {
    setAutoRefreshEnabled((prev) => !prev);
  }, []);

  const autoRefreshAvailable = dataSource === "api";

  return (
    <div className="app-shell">
      <Sidebar
        payload={payload}
        dataSource={dataSource}
        isRefreshing={isRefreshing}
        lastLoadedAt={lastLoadedAt}
        onRefresh={refreshPayload}
        autoRefreshEnabled={autoRefreshEnabled}
        autoRefreshIntervalSeconds={AUTO_REFRESH_INTERVAL_MS / 1000}
        autoRefreshAvailable={autoRefreshAvailable}
        onToggleAutoRefresh={handleToggleAutoRefresh}
      />

      <main className="main-panel">
        <h2 className="panel-heading">Today's Snapshot</h2>
        <MetricGrid metricCards={payload.metric_cards} />
        <h3 className="section-heading">Last Games</h3>
        <GameList matches={payload.recent_matches} />
      </main>

      <DetailsPanel
        sessionSummary={payload.session_summary}
        dataSource={dataSource}
      />
    </div>
  );
}