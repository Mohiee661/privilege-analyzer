export interface Finding {
  finding_id: string;
  person_id: string;
  name: string;
  email: string;
  risk_type: string;
  severity: string;
  description: string;
  evidence: Record<string, unknown>;
}
