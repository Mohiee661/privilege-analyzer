export interface Dashboard {
  total_identities: number;
  critical_risks: number;
  high_risks: number;
  offboarding_gaps: number;
  admin_accounts: number;
}

export interface Accuracy {
  precision: number;
  recall: number;
  f1: number;
  trap_suppression_rate: number;
}

export interface Analytics {
  risk_distribution: Record<string, number>;
  platform_distribution: Record<string, number>;
  top_risk_types: Record<string, number>;
}
