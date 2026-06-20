import { loadRiskCenterPageData as loadRiskCenterPageDataFromLib } from "@/lib/api";
import { requestJson } from "./client";
import type { RiskProfile, RiskProfileDetailResponse } from "@/types";

export async function listRisks(level?: string): Promise<RiskProfile[]> {
  const suffix = level ? `?level=${encodeURIComponent(level)}` : "";
  return requestJson<RiskProfile[]>(`/risks${suffix}`);
}

export async function getRiskDetail(personId: string): Promise<RiskProfileDetailResponse> {
  return requestJson<RiskProfileDetailResponse>(`/risks/${personId}`);
}

export const loadRiskCenterPageData = loadRiskCenterPageDataFromLib;
