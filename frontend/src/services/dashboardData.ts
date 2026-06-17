import type { DashboardCompactPayload } from "../types/dashboardPayload";
import { mockDashboardPayload } from "../mock/mockDashboardPayload";

const API_URL          = "http://127.0.0.1:8765/api/dashboard";
const DASHBOARD_JSON   = "/dashboard_payload.json";

export type DashboardDataSource = "api" | "json" | "mock";

export interface DashboardLoadResult {
  payload: DashboardCompactPayload;
  source: DashboardDataSource;
}

export async function loadDashboardPayloadWithSource(): Promise<DashboardLoadResult> {
  // 1. Try local API
  try {
    const res = await fetch(API_URL, { cache: "no-store" });
    if (res.ok) {
      const data = (await res.json()) as DashboardCompactPayload;
      return { payload: data, source: "api" };
    }
  } catch {
    // fall through
  }

  // 2. Try static JSON
  try {
    const res = await fetch(DASHBOARD_JSON, { cache: "no-store" });
    if (res.ok) {
      const data = (await res.json()) as DashboardCompactPayload;
      return { payload: data, source: "json" };
    }
  } catch {
    // fall through
  }

  // 3. Mock fallback
  return { payload: mockDashboardPayload, source: "mock" };
}

// Backward-compatible wrapper — keeps existing callers working
export async function loadDashboardPayload(): Promise<DashboardCompactPayload> {
  const { payload } = await loadDashboardPayloadWithSource();
  return payload;
}