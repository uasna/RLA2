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

export default function App() {
  const [payload, setPayload] =
    React.useState<DashboardCompactPayload>(mockDashboardPayload);
  const [dataSource, setDataSource] = React.useState<DashboardDataSource>("mock");
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [lastLoadedAt, setLastLoadedAt] = React.useState<Date | null>(null);

  const refreshPayload = React.useCallback(async () => {
    setIsRefreshing(true);
    try {
      const { payload: loaded, source } = await loadDashboardPayloadWithSource();
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