import { loadDashboardPageData as loadDashboardPageDataFromLib } from "@/lib/api";
import { requestJson } from "./client";
import type { Analytics, Dashboard } from "@/types";

export async function getDashboard(): Promise<Dashboard> {
  return requestJson<Dashboard>("/dashboard");
}

export async function getAnalytics(): Promise<Analytics> {
  return requestJson<Analytics>("/analytics");
}

export const loadDashboardPageData = loadDashboardPageDataFromLib;
