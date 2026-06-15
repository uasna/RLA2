import React from "react";
import "./styles.css";
import type { DashboardCompactPayload } from "./types/dashboardPayload";
import { mockDashboardPayload } from "./mock/mockDashboardPayload";
import { loadDashboardPayload } from "./services/dashboardData";
import Sidebar from "./components/Sidebar";
import MetricGrid from "./components/MetricGrid";
import GameList from "./components/GameList";
import DetailsPanel from "./components/DetailsPanel";

export default function App() {
  const [payload, setPayload] =
    React.useState<DashboardCompactPayload>(mockDashboardPayload);
  const [dataSource, setDataSource] = React.useState<"mock" | "json">("mock");
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [lastLoadedAt, setLastLoadedAt] = React.useState<Date | null>(null);

  const refreshPayload = React.useCallback(async () => {
    setIsRefreshing(true);
    try {
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
          loaded = await loadDashboardPayload();
        }
      } catch {
        loaded = await loadDashboardPayload();
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

  return (
    <div className="app-shell">
      <Sidebar
        payload={payload}
        dataSource={dataSource}
        isRefreshing={isRefreshing}
        lastLoadedAt={lastLoadedAt}
        onRefresh={refreshPayload}
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