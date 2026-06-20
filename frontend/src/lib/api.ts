import type {
  AIAnalysis,
  AIReport,
  DashboardMetrics,
  DepartmentRisk,
  Finding,
  FindingType,
  Identity,
  MetricPoint,
  Platform,
  RiskProfile,
  RiskLevel,
  ShowcaseIncident,
  TimelineEvent,
  TrendPoint,
  WorkspaceData,
} from "@/lib/models";
import { requestJson } from "@/services/client";

type ApiPlatformKey = "ad" | "azure" | "aws" | "okta" | "salesforce";

interface ApiIdentityAccount {
  status: string;
  role: string;
  last_login?: string;
}

interface ApiIdentity {
  person_id: string;
  name: string;
  email: string;
  accounts: Record<ApiPlatformKey, ApiIdentityAccount>;
}

interface ApiRiskProfile {
  person_id: string;
  name: string;
  email: string;
  score: number;
  risk_level: string;
  findings: string[];
}

interface ApiFinding {
  finding_id: string;
  person_id: string;
  name: string;
  email: string;
  risk_type: string;
  severity: string;
  description: string;
  evidence: Record<string, unknown>;
}

interface ApiAIReport {
  person_id: string;
  risk_score: number;
  risk_level: string;
  summary: string;
  security_impact: string;
  recommended_actions: string[];
}

interface ApiDashboard {
  total_identities: number;
  critical_risks: number;
  high_risks: number;
  offboarding_gaps: number;
  admin_accounts: number;
}

interface ApiAnalytics {
  risk_distribution: Record<string, number>;
  platform_distribution: Record<string, number>;
  top_risk_types: Record<string, number>;
}

interface ApiIdentityListResponse {
  items: ApiIdentity[];
  page: number;
  page_size: number;
  total: number;
}

const DEFAULT_PAGE_SIZE = 100;

const PLATFORM_LABELS: Record<ApiPlatformKey, Platform> = {
  ad: "AD",
  azure: "Azure",
  aws: "AWS",
  okta: "Okta",
  salesforce: "Salesforce",
};

const FINDING_TYPE_LABELS: Record<string, FindingType> = {
  offboarding_gap: "OFFBOARDING_GAP",
  multi_platform_admin: "MULTI_PLATFORM_ADMIN",
  stale_active_account: "STALE_ACTIVE_ACCOUNT",
  suspended_account_mismatch: "SUSPENDED_ACCOUNT_MISMATCH",
  excessive_platform_exposure: "EXCESSIVE_PLATFORM_EXPOSURE",
};

const RISK_LEVEL_LABELS: Record<string, RiskLevel> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  none: "Informational",
  informational: "Informational",
};

const FallbackRecommendation: Record<FindingType, string> = {
  OFFBOARDING_GAP: "Immediately disable remaining active accounts and complete offboarding.",
  MULTI_PLATFORM_ADMIN:
    "Review administrative privileges and convert standing access to just-in-time elevation.",
  STALE_ACTIVE_ACCOUNT:
    "Disable or review the unused active account and confirm ongoing business need.",
  SUSPENDED_ACCOUNT_MISMATCH:
    "Reconcile suspension state across identity providers and downstream platforms.",
  EXCESSIVE_PLATFORM_EXPOSURE: "Reduce access to only the platforms required for the current role.",
};

const workspaceCache = {
  promise: null as Promise<WorkspaceData> | null,
};

async function fetchAllIdentities(): Promise<ApiIdentity[]> {
  const items: ApiIdentity[] = [];
  let page = 1;
  let total = Number.POSITIVE_INFINITY;

  while (items.length < total) {
    const response = await requestJson<ApiIdentityListResponse>(
      `/identities?page=${page}&page_size=${DEFAULT_PAGE_SIZE}`,
    );
    items.push(...response.items);
    total = response.total;
    if (response.items.length === 0) {
      break;
    }
    page += 1;
  }

  return items;
}

function toRiskLevel(value: string): RiskLevel {
  return RISK_LEVEL_LABELS[value.toLowerCase()] ?? "Informational";
}

function toFindingType(value: string): FindingType {
  const normalized = FINDING_TYPE_LABELS[value.toLowerCase()];
  if (normalized) return normalized;
  return "EXCESSIVE_PLATFORM_EXPOSURE";
}

function platformLabel(key: string): Platform | null {
  return PLATFORM_LABELS[key.toLowerCase() as ApiPlatformKey] ?? null;
}

function normalizeStatus(value: string): "Active" | "Disabled" | "Suspended" {
  const lower = value.toLowerCase();
  if (lower === "disabled") return "Disabled";
  if (lower === "suspended") return "Suspended";
  return "Active";
}

function stringifyEvidence(evidence: Record<string, unknown>): string {
  const entries = Object.entries(evidence);
  if (entries.length === 0) return "No evidence provided.";
  return entries
    .map(([key, value]) => `${key}: ${typeof value === "string" ? value : JSON.stringify(value)}`)
    .join(" | ");
}

function latestLogin(accounts: Record<string, ApiIdentityAccount>): string {
  const timestamps = Object.values(accounts)
    .map((account) => account.last_login)
    .filter((value): value is string => Boolean(value));
  if (timestamps.length === 0) {
    return new Date().toISOString();
  }
  return timestamps.sort().at(-1) ?? new Date().toISOString();
}

function strongestRole(accounts: Record<string, ApiIdentityAccount>): string {
  const roles = Object.values(accounts).map((account) => account.role);
  const prioritized = [
    "Global Administrator",
    "Security Administrator",
    "Administrator",
    "Admin",
    "Developer",
    "Security Analyst",
    "Support Engineer",
    "Manager",
    "Employee",
    "Contractor",
  ];

  for (const candidate of prioritized) {
    const match = roles.find((role) => role.toLowerCase().includes(candidate.toLowerCase()));
    if (match) return match;
  }

  return roles[0] ?? "Employee";
}

function deriveDepartment(accounts: Record<string, ApiIdentityAccount>): string {
  const roles = Object.values(accounts).map((account) => account.role.toLowerCase());
  if (roles.some((role) => role.includes("security"))) return "Security";
  if (
    roles.some(
      (role) => role.includes("developer") || role.includes("engineer") || role.includes("devops"),
    )
  )
    return "Engineering";
  if (
    roles.some(
      (role) =>
        role.includes("support") ||
        role.includes("it") ||
        role.includes("administrator") ||
        role.includes("admin"),
    )
  )
    return "IT";
  if (
    roles.some(
      (role) =>
        role.includes("finance") || role.includes("controller") || role.includes("accountant"),
    )
  )
    return "Finance";
  if (roles.some((role) => role.includes("hr") || role.includes("people"))) return "HR";
  if (
    roles.some(
      (role) =>
        role.includes("sales") ||
        role.includes("account executive") ||
        role.includes("customer success"),
    )
  )
    return "Sales";
  if (roles.some((role) => role.includes("contractor"))) return "Operations";
  return "Operations";
}

function deriveTitle(accounts: Record<string, ApiIdentityAccount>): string {
  const role = strongestRole(accounts).toLowerCase();
  if (role.includes("global administrator")) return "Global Administrator";
  if (role.includes("security administrator")) return "Security Administrator";
  if (role.includes("administrator") || role.includes("admin")) return "Administrator";
  if (role.includes("developer")) return "Developer";
  if (role.includes("security analyst")) return "Security Analyst";
  if (role.includes("support")) return "Support Engineer";
  if (role.includes("manager")) return "Manager";
  if (role.includes("contractor")) return "Contractor";
  return "Employee";
}

function deriveIdentityStatus(
  accounts: Record<string, ApiIdentityAccount>,
): "Active" | "Offboarded" | "Suspended" {
  const statuses = Object.values(accounts).map((account) => normalizeStatus(account.status));
  if (statuses.includes("Suspended")) return "Suspended";
  if (statuses.every((status) => status === "Disabled")) return "Offboarded";
  return "Active";
}

function createPlatformAccess(accounts: Record<string, ApiIdentityAccount>) {
  return Object.entries(accounts)
    .map(([key, account]) => {
      const platform = platformLabel(key);
      if (!platform) return null;
      return {
        platform,
        status: normalizeStatus(account.status),
        role: account.role,
        lastLogin: account.last_login ?? new Date().toISOString(),
      };
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
}

function recommendationForFindingType(type: FindingType): string {
  return FallbackRecommendation[type];
}

function platformList(access: ReturnType<typeof createPlatformAccess>): Platform[] {
  return access.map((item) => item.platform);
}

function convertFinding(apiFinding: ApiFinding, identity: Identity | undefined): Finding {
  const type = toFindingType(apiFinding.risk_type);
  const access = identity?.platformAccess ?? [];
  const evidencePlatforms = Object.entries(apiFinding.evidence)
    .filter(([, value]) => typeof value === "string")
    .map(([key]) => platformLabel(key))
    .filter((value): value is Platform => Boolean(value));
  const platforms =
    evidencePlatforms.length > 0 ? evidencePlatforms : access.map((item) => item.platform);

  return {
    id: apiFinding.finding_id,
    type,
    severity: toRiskLevel(apiFinding.severity),
    description: apiFinding.description,
    evidence: stringifyEvidence(apiFinding.evidence),
    recommendation: recommendationForFindingType(type),
    identityId: apiFinding.person_id,
    platforms,
    createdAt: identity?.lastLogin ?? new Date().toISOString(),
  };
}

function convertRiskProfile(apiProfile: ApiRiskProfile): RiskProfile {
  return {
    personId: apiProfile.person_id,
    name: apiProfile.name,
    email: apiProfile.email,
    score: apiProfile.score,
    riskLevel: toRiskLevel(apiProfile.risk_level),
    findings: apiProfile.findings.map((finding) => toFindingType(finding)),
  };
}

function convertAIReport(
  apiReport: ApiAIReport | undefined,
  identity: Identity,
  findings: Finding[],
): AIAnalysis {
  if (apiReport) {
    return {
      summary: apiReport.summary,
      impact: apiReport.security_impact,
      explanation: `Risk score ${apiReport.risk_score} reflects ${findings.length} linked findings across ${identity.platforms.length} platforms.`,
      actions: apiReport.recommended_actions,
      notes: "AI insight sourced from backend copilot export.",
    };
  }

  return {
    summary: `${identity.name} presents a ${identity.riskLevel.toLowerCase()} identity risk profile driven by ${findings.length} linked findings across ${identity.platforms.length} platforms.`,
    impact: `If ignored, the identity could retain unnecessary access across ${identity.platforms.join(", ")}.`,
    explanation: `The score of ${identity.riskScore} is derived from correlated identity findings and platform exposure.`,
    actions: [
      "Review the identity and confirm current business need.",
      "Remove privileges not required for the role.",
      "Validate account status and recent activity.",
    ],
    notes: "Fallback analysis generated locally because the backend AI report is unavailable.",
  };
}

function aggregateMetrics(
  identities: Identity[],
  findings: Finding[],
  riskProfiles: RiskProfile[],
): DashboardMetrics {
  const criticalRisks = riskProfiles.filter((profile) => profile.riskLevel === "Critical").length;
  const highRisks = riskProfiles.filter((profile) => profile.riskLevel === "High").length;
  const offboardingGaps = findings.filter((finding) => finding.type === "OFFBOARDING_GAP").length;
  const adminAccounts = identities.filter((identity) =>
    identity.platformAccess.some((access) => /administrator|admin|owner/i.test(access.role)),
  ).length;

  return {
    totalIdentities: identities.length,
    criticalRisks,
    highRisks,
    offboardingGaps,
    adminAccounts,
  };
}

function toMetricPoints(record: Record<string, number>): MetricPoint[] {
  return Object.entries(record)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);
}

function buildDepartmentRisk(identities: Identity[]): DepartmentRisk[] {
  const grouped = new Map<string, number[]>();
  for (const identity of identities) {
    const list = grouped.get(identity.department) ?? [];
    list.push(identity.riskScore);
    grouped.set(identity.department, list);
  }

  return Array.from(grouped.entries())
    .map(([name, scores]) => ({
      name,
      value: Math.round(scores.reduce((sum, score) => sum + score, 0) / Math.max(scores.length, 1)),
    }))
    .sort((a, b) => b.value - a.value);
}

function buildRiskTrends(findings: Finding[]): TrendPoint[] {
  const monthly = new Map<string, number>();
  for (const finding of findings) {
    const month = finding.createdAt.slice(0, 7);
    monthly.set(month, (monthly.get(month) ?? 0) + 1);
  }
  return Array.from(monthly.entries())
    .map(([month, events]) => ({ month, events }))
    .sort((a, b) => a.month.localeCompare(b.month));
}

function buildTopDepartmentsAtRisk(identities: Identity[], limit = 5): DepartmentRisk[] {
  return buildDepartmentRisk(identities).slice(0, limit);
}

function buildShowcaseIncidents(workspace: WorkspaceData): ShowcaseIncident[] {
  return workspace.topCritical.slice(0, 10).map((identity) => {
    const findings = workspace.findingsByIdentityId[identity.id] ?? [];
    return {
      scenarioId: identity.id,
      title: `${identity.name} Showcase`,
      personId: identity.id,
      name: identity.name,
      email: identity.email,
      riskScore: identity.riskScore,
      riskLevel: identity.riskLevel,
      findingType: findings[0]?.type ?? "EXCESSIVE_PLATFORM_EXPOSURE",
      summary: findings[0]?.description ?? "High-priority identity incident.",
      accounts: Object.fromEntries(
        identity.platformAccess.map((access) => [
          access.platform.toLowerCase(),
          { status: access.status.toLowerCase(), role: access.role, lastLogin: access.lastLogin },
        ]),
      ),
      timeline: buildTimeline(identity, findings).map((event) => ({
        date: event.timestamp.slice(0, 10),
        event: event.description,
      })),
    };
  });
}

function buildTimeline(identity: Identity, findings: Finding[]): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  identity.platformAccess.forEach((access, index) => {
    if (access.lastLogin) {
      events.push({
        id: `${identity.id}-login-${index}`,
        timestamp: access.lastLogin,
        platform: access.platform,
        type: `${access.platform} Activity`,
        description: `${access.platform} account ${access.status.toLowerCase()} for ${identity.name}`,
        severity:
          access.status === "Suspended"
            ? "High"
            : access.status === "Disabled"
              ? "Medium"
              : "Informational",
      });
    }
  });

  findings.forEach((finding, index) => {
    events.push({
      id: `${identity.id}-finding-${index}`,
      timestamp: finding.createdAt,
      platform: "System",
      type: finding.type.replace(/_/g, " "),
      description: finding.description,
      severity: finding.severity,
    });
  });

  return events.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
}

async function loadRawWorkspace() {
  const [identities, riskProfiles, findings, aiReports, dashboard, analytics] = await Promise.all([
    fetchAllIdentities(),
    requestJson<ApiRiskProfile[]>("/risks"),
    requestJson<ApiFinding[]>("/findings"),
    requestJson<ApiAIReport[]>("/ai-reports"),
    requestJson<ApiDashboard>("/dashboard"),
    requestJson<ApiAnalytics>("/analytics"),
  ]);

  return { identities, riskProfiles, findings, aiReports, dashboard, analytics };
}

export async function loadWorkspaceData(): Promise<WorkspaceData> {
  if (!workspaceCache.promise) {
    workspaceCache.promise = loadRawWorkspace().then(
      ({
        identities: apiIdentities,
        riskProfiles: apiRiskProfiles,
        findings: apiFindings,
        aiReports: apiAiReports,
        dashboard,
        analytics,
      }) => {
        const riskProfiles = apiRiskProfiles.map(convertRiskProfile);
        const identities = apiIdentities.map((identity) => {
          const platformAccess = createPlatformAccess(identity.accounts);
          const riskProfile = riskProfiles.find(
            (profile) => profile.personId === identity.person_id,
          );
          const personFindings = apiFindings.filter(
            (finding) => finding.person_id === identity.person_id,
          );
          const findingViews = personFindings.map((finding) => convertFinding(finding, undefined));
          return {
            id: identity.person_id,
            name: identity.name,
            email: identity.email,
            department: deriveDepartment(identity.accounts),
            status: deriveIdentityStatus(identity.accounts),
            riskScore: riskProfile?.score ?? 0,
            riskLevel: riskProfile?.riskLevel ?? "Informational",
            platforms: platformList(platformAccess),
            platformAccess,
            lastLogin: latestLogin(identity.accounts),
            findingCount: riskProfile?.findings.length ?? findingViews.length,
            title: deriveTitle(identity.accounts),
          } satisfies Identity;
        });

        const identityById = Object.fromEntries(
          identities.map((identity) => [identity.id, identity]),
        );
        const findings = apiFindings.map((finding) =>
          convertFinding(finding, identityById[finding.person_id]),
        );
        const findingsByIdentityId = findings.reduce<Record<string, Finding[]>>((acc, finding) => {
          const list = acc[finding.identityId] ?? [];
          list.push(finding);
          acc[finding.identityId] = list;
          return acc;
        }, {});

        const aiReports = apiAiReports.map((report) => ({
          personId: report.person_id,
          riskScore: report.risk_score,
          riskLevel: toRiskLevel(report.risk_level),
          summary: report.summary,
          securityImpact: report.security_impact,
          recommendedActions: report.recommended_actions,
        }));
        const aiReportById = Object.fromEntries(
          aiReports.map((report) => [report.personId, report]),
        );
        const topCritical = [...identities].sort((a, b) => b.riskScore - a.riskScore).slice(0, 5);
        const topCriticalWithCounts = topCritical.map((identity) => ({
          ...identity,
          findingCount: findingsByIdentityId[identity.id]?.length ?? identity.findingCount,
        }));

        const workspace: WorkspaceData = {
          dashboard: {
            totalIdentities: dashboard.total_identities,
            criticalRisks: dashboard.critical_risks,
            highRisks: dashboard.high_risks,
            offboardingGaps: dashboard.offboarding_gaps,
            adminAccounts: dashboard.admin_accounts,
          },
          riskDistribution: toMetricPoints(analytics.risk_distribution).map((point) => ({
            name: toRiskLevel(point.name),
            value: point.value,
          })),
          platformDistribution: toMetricPoints(analytics.platform_distribution).map((point) => ({
            name: (PLATFORM_LABELS[point.name.toLowerCase() as ApiPlatformKey] ??
              point.name) as Platform,
            value: point.value,
          })),
          topRiskCategories: toMetricPoints(analytics.top_risk_types),
          departmentRisk: buildDepartmentRisk(identities),
          topCritical: topCriticalWithCounts,
          identities,
          findings,
          aiReports,
          identityById,
          findingsByIdentityId,
          aiReportById,
          riskProfiles,
          topDepartmentsAtRisk: buildTopDepartmentsAtRisk(identities),
          riskTrends: buildRiskTrends(findings),
          platformRiskBreakdown: toMetricPoints(analytics.platform_distribution),
          showcaseIncidents: [],
        };

        workspace.showcaseIncidents = buildShowcaseIncidents(workspace);
        return workspace;
      },
    );
  }

  return workspaceCache.promise;
}

export async function loadDashboardPageData() {
  const workspace = await loadWorkspaceData();
  return workspace;
}

export async function loadRiskCenterPageData() {
  const workspace = await loadWorkspaceData();
  return workspace;
}

export async function loadIdentityExplorerPageData() {
  const workspace = await loadWorkspaceData();
  return workspace;
}

export async function loadFindingsPageData() {
  const workspace = await loadWorkspaceData();
  return workspace;
}

export async function loadCopilotPageData() {
  const workspace = await loadWorkspaceData();
  return workspace;
}

export async function loadIdentityDetailPageData(personId: string) {
  const workspace = await loadWorkspaceData();
  const identity = workspace.identityById[personId] ?? null;
  if (!identity) return null;
  return {
    identity,
    findings: workspace.findingsByIdentityId[personId] ?? [],
    timeline: buildTimeline(identity, workspace.findingsByIdentityId[personId] ?? []),
    aiAnalysis: convertAIReport(
      workspace.aiReportById[personId],
      identity,
      workspace.findingsByIdentityId[personId] ?? [],
    ),
  };
}

export async function loadReportsPageData() {
  const workspace = await loadWorkspaceData();
  return workspace;
}

export async function searchIdentities(query: string) {
  const workspace = await loadWorkspaceData();
  const normalized = query.trim().toLowerCase();
  if (!normalized) return [];
  return workspace.identities.filter((identity) =>
    `${identity.name} ${identity.email} ${identity.department} ${identity.id}`
      .toLowerCase()
      .includes(normalized),
  );
}
