import type { DashboardCompactPayload } from "../types/dashboardPayload";
import { mockDashboardPayload } from "../mock/mockDashboardPayload";

const DASHBOARD_PAYLOAD_PATH = "./dashboard_payload.json";

export async function loadDashboardPayload(): Promise<DashboardCompactPayload> {
  try {
    const res = await fetch(DASHBOARD_PAYLOAD_PATH, {
      cache: "no-store",
    });

    if (!res.ok) return mockDashboardPayload;

    const data = (await res.json()) as DashboardCompactPayload;
    return data;
  } catch {
    return mockDashboardPayload;
  }
}