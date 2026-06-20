import { loadReportsPageData as loadReportsPageDataFromLib } from "@/lib/api";
import { requestJson } from "./client";
import type { Analytics } from "@/types";

export async function getAnalytics(): Promise<Analytics> {
  return requestJson<Analytics>("/analytics");
}

export const loadAnalyticsPageData = loadReportsPageDataFromLib;
