import type { Finding } from "./finding";

export interface RiskProfile {
  person_id: string;
  name: string;
  email: string;
  score: number;
  risk_level: string;
  findings: string[];
}

export interface RiskProfileDetailResponse {
  profile: RiskProfile;
  findings: Finding[];
  ai_report: {
    person_id: string;
    risk_score: number;
    risk_level: string;
    summary: string;
    security_impact: string;
    recommended_actions: string[];
  } | null;
}
