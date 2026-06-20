import { loadFindingsPageData as loadFindingsPageDataFromLib } from "@/lib/api";
import { requestJson } from "./client";
import type { Finding } from "@/types";

export async function listFindings(riskType?: string): Promise<Finding[]> {
  const suffix = riskType ? `?risk_type=${encodeURIComponent(riskType)}` : "";
  return requestJson<Finding[]>(`/findings${suffix}`);
}

export const loadFindingsPageData = loadFindingsPageDataFromLib;
