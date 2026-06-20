export interface AIReport {
  person_id: string;
  risk_score: number;
  risk_level: string;
  summary: string;
  security_impact: string;
  recommended_actions: string[];
}
