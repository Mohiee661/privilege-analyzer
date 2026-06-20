export type Platform = "AD" | "Azure" | "AWS" | "Okta" | "Salesforce";
export type RiskLevel = "Critical" | "High" | "Medium" | "Low" | "Informational";
export type FindingType =
  | "OFFBOARDING_GAP"
  | "MULTI_PLATFORM_ADMIN"
  | "STALE_ACTIVE_ACCOUNT"
  | "SUSPENDED_ACCOUNT_MISMATCH"
  | "EXCESSIVE_PLATFORM_EXPOSURE";

export interface PlatformAccess {
  platform: Platform;
  status: "Active" | "Disabled" | "Suspended";
  role: string;
  lastLogin: string;
}

export interface Finding {
  id: string;
  type: FindingType;
  severity: RiskLevel;
  description: string;
  evidence: string;
  recommendation: string;
  identityId: string;
  platforms: Platform[];
  createdAt: string;
}

export interface Identity {
  id: string;
  name: string;
  email: string;
  department: string;
  status: "Active" | "Offboarded" | "Suspended";
  riskScore: number;
  riskLevel: RiskLevel;
  platforms: Platform[];
  platformAccess: PlatformAccess[];
  lastLogin: string;
  findingCount: number;
  title: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  platform: Platform | "System";
  type: string;
  description: string;
  severity: RiskLevel;
}

export interface AIAnalysis {
  summary: string;
  impact: string;
  explanation: string;
  actions: string[];
  notes: string;
}

export interface MetricPoint {
  name: string;
  value: number;
}

export interface DashboardMetrics {
  totalIdentities: number;
  criticalRisks: number;
  highRisks: number;
  offboardingGaps: number;
  adminAccounts: number;
}

export interface WorkspaceData {
  dashboard: DashboardMetrics;
  riskDistribution: MetricPoint[];
  platformDistribution: MetricPoint[];
  topRiskCategories: MetricPoint[];
  departmentRisk: MetricPoint[];
  topCritical: Identity[];
  identities: Identity[];
  findings: Finding[];
  aiReports: AIReport[];
  identityById: Record<string, Identity>;
  findingsByIdentityId: Record<string, Finding[]>;
  aiReportById: Record<string, AIReport>;
  riskProfiles: RiskProfile[];
  topDepartmentsAtRisk: DepartmentRisk[];
  riskTrends: TrendPoint[];
  platformRiskBreakdown: MetricPoint[];
  showcaseIncidents: ShowcaseIncident[];
}

export interface RiskProfile {
  personId: string;
  name: string;
  email: string;
  score: number;
  riskLevel: RiskLevel;
  findings: FindingType[];
}

export interface AIReport {
  personId: string;
  riskScore: number;
  riskLevel: RiskLevel;
  summary: string;
  securityImpact: string;
  recommendedActions: string[];
}

export interface TrendPoint {
  month: string;
  events: number;
}

export interface DepartmentRisk {
  name: string;
  value: number;
}

export interface ShowcaseIncident {
  scenarioId: string;
  title: string;
  personId: string;
  name: string;
  email: string;
  riskScore: number;
  riskLevel: RiskLevel;
  findingType: FindingType;
  summary: string;
  accounts: Record<string, { status: string; role: string; lastLogin?: string }>;
  timeline: Array<{ date: string; event: string }>;
}
