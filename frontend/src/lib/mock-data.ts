export type Platform = "AD" | "Azure" | "AWS" | "Okta" | "Salesforce";
export type RiskLevel = "Critical" | "High" | "Medium" | "Low" | "Informational";
export type FindingType =
  | "OFFBOARDING_GAP"
  | "MULTI_PLATFORM_ADMIN"
  | "STALE_ACCOUNT"
  | "TOKEN_ABUSE"
  | "PRIVILEGE_ESCALATION"
  | "SUSPENDED_ACCOUNT_MISMATCH"
  | "PLATFORM_EXPOSURE";

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

const departments = [
  "Engineering",
  "IT",
  "Finance",
  "HR",
  "Security",
  "Operations",
  "Sales",
  "Marketing",
];
const platforms: Platform[] = ["AD", "Azure", "AWS", "Okta", "Salesforce"];

const firstNames = [
  "Sarah",
  "Marcus",
  "Elena",
  "David",
  "Priya",
  "James",
  "Aisha",
  "Liam",
  "Naomi",
  "Hiroshi",
  "Carlos",
  "Yuki",
  "Anya",
  "Benjamin",
  "Fatima",
  "Daniel",
  "Sophia",
  "Olivia",
  "Rajesh",
  "Chen",
  "Amelia",
  "Ethan",
  "Zara",
  "Noah",
  "Mia",
  "Lucas",
  "Emma",
  "Isabella",
  "Mason",
  "Charlotte",
];
const lastNames = [
  "Chen",
  "Patel",
  "Rodriguez",
  "Anderson",
  "Volkov",
  "Okafor",
  "Nakamura",
  "Kowalski",
  "Singh",
  "Müller",
  "Tanaka",
  "Hassan",
  "Schmidt",
  "García",
  "Johansson",
  "Park",
  "Reyes",
  "Whitaker",
  "Brennan",
  "Sullivan",
  "Hoffman",
  "Castillo",
  "Bennett",
  "Foster",
  "Holloway",
  "Carter",
  "Hayes",
  "Mitchell",
  "Cooper",
  "Russell",
];

function rng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}
const rand = rng(42);
const pick = <T>(a: T[]) => a[Math.floor(rand() * a.length)];
const pickN = <T>(a: T[], n: number) => [...a].sort(() => rand() - 0.5).slice(0, n);

function riskLevelFromScore(score: number): RiskLevel {
  if (score >= 90) return "Critical";
  if (score >= 70) return "High";
  if (score >= 40) return "Medium";
  if (score >= 20) return "Low";
  return "Informational";
}

function daysAgo(d: number) {
  const date = new Date();
  date.setDate(date.getDate() - d);
  return date.toISOString();
}

export const identities: Identity[] = Array.from({ length: 64 }, (_, i) => {
  const fn = firstNames[i % firstNames.length];
  const ln = lastNames[(i * 3) % lastNames.length];
  const name = `${fn} ${ln}`;
  const score = Math.floor(rand() * 100);
  const dept = departments[i % departments.length];
  const plats = pickN(platforms, 2 + Math.floor(rand() * 4));
  const status = rand() > 0.85 ? "Offboarded" : rand() > 0.9 ? "Suspended" : "Active";
  return {
    id: `id-${1000 + i}`,
    name,
    email: `${fn.toLowerCase()}.${ln.toLowerCase()}@contoso.com`,
    department: dept,
    status,
    riskScore: score,
    riskLevel: riskLevelFromScore(score),
    platforms: plats,
    platformAccess: plats.map((p) => ({
      platform: p,
      status: rand() > 0.85 ? "Disabled" : "Active",
      role: pick([
        "Administrator",
        "Reader",
        "Contributor",
        "Analyst",
        "Owner",
        "User",
        "Developer",
        "Auditor",
      ]),
      lastLogin: daysAgo(Math.floor(rand() * 60)),
    })),
    lastLogin: daysAgo(Math.floor(rand() * 60)),
    findingCount: Math.floor(rand() * 8) + (score > 80 ? 3 : 0),
    title: pick([
      "Senior Engineer",
      "VP Engineering",
      "Cloud Architect",
      "Security Analyst",
      "IT Administrator",
      "Director",
      "Financial Controller",
      "DevOps Lead",
      "HR Manager",
      "Account Executive",
    ]),
  };
});

const findingTemplates: Record<
  FindingType,
  { description: string; evidence: string; recommendation: string }
> = {
  OFFBOARDING_GAP: {
    description:
      "Identity marked as offboarded in HR system but retains active access on cloud platforms",
    evidence:
      "AD account disabled 23 days ago, but AWS IAM access key used 2 hours ago from new IP",
    recommendation:
      "Immediately revoke all cloud platform credentials and rotate associated API keys",
  },
  MULTI_PLATFORM_ADMIN: {
    description:
      "Identity holds administrative privileges across three or more enterprise platforms",
    evidence:
      "Administrator role detected on AWS, Azure, and Okta — exceeds least-privilege threshold",
    recommendation:
      "Conduct privilege review and convert standing access to just-in-time elevation",
  },
  STALE_ACCOUNT: {
    description: "Active account with no authentication activity for over 90 days",
    evidence: "Last successful login: 127 days ago. Account remains enabled with full permissions",
    recommendation: "Disable account and schedule for deprovisioning per organizational policy",
  },
  TOKEN_ABUSE: {
    description: "Anomalous API token usage pattern detected across cloud platforms",
    evidence: "Service token authenticated from 4 distinct geographic regions within 6-hour window",
    recommendation: "Revoke token, audit recent API calls, and enforce IP allowlisting",
  },
  PRIVILEGE_ESCALATION: {
    description: "Recent unauthorized privilege escalation detected on cloud workload",
    evidence:
      "User-assigned AdministratorAccess policy attached outside change-management workflow",
    recommendation: "Roll back privilege change and review IAM policy assignment controls",
  },
  SUSPENDED_ACCOUNT_MISMATCH: {
    description: "Account suspended in primary IdP but remains active in downstream platforms",
    evidence: "Okta status: Suspended. Salesforce status: Active. SSO bypass risk identified",
    recommendation:
      "Reconcile downstream platform states with primary IdP and remove direct logins",
  },
  PLATFORM_EXPOSURE: {
    description: "Identity has access to an unusually high number of platforms for role profile",
    evidence: "5 platforms granted; department peer median is 2 platforms",
    recommendation:
      "Review access justification and revoke platforms not required for current role",
  },
};

const findingTypes = Object.keys(findingTemplates) as FindingType[];

export const findings: Finding[] = identities.flatMap((id) =>
  Array.from({ length: id.findingCount }, (_, i) => {
    const type = findingTypes[(id.riskScore + i) % findingTypes.length];
    const tpl = findingTemplates[type];
    const sev: RiskLevel =
      id.riskScore >= 90
        ? i === 0
          ? "Critical"
          : "High"
        : id.riskScore >= 70
          ? "High"
          : id.riskScore >= 40
            ? "Medium"
            : "Low";
    return {
      id: `f-${id.id}-${i}`,
      type,
      severity: sev,
      description: tpl.description,
      evidence: tpl.evidence,
      recommendation: tpl.recommendation,
      identityId: id.id,
      platforms: pickN(id.platforms, Math.min(id.platforms.length, 1 + Math.floor(rand() * 2))),
      createdAt: daysAgo(Math.floor(rand() * 30)),
    };
  }),
);

export function getTimeline(identityId: string): TimelineEvent[] {
  const id = identities.find((x) => x.id === identityId);
  if (!id) return [];
  const types = [
    { type: "Account Created", sev: "Informational" as RiskLevel, plat: "AD" as const },
    { type: "Admin Rights Granted", sev: "High" as RiskLevel, plat: "AWS" as const },
    { type: "AD Account Disabled", sev: "Medium" as RiskLevel, plat: "AD" as const },
    { type: "AWS Login Detected", sev: "Critical" as RiskLevel, plat: "AWS" as const },
    { type: "API Token Used", sev: "High" as RiskLevel, plat: "Okta" as const },
    { type: "Suspicious Access Pattern", sev: "Critical" as RiskLevel, plat: "Azure" as const },
    { type: "MFA Challenge Failed", sev: "Medium" as RiskLevel, plat: "Okta" as const },
    { type: "Policy Change Applied", sev: "Informational" as RiskLevel, plat: "System" as const },
  ];
  return types.map((t, i) => ({
    id: `tl-${identityId}-${i}`,
    timestamp: daysAgo(types.length - i),
    platform: t.plat,
    type: t.type,
    description: `${t.type} on ${t.plat} for ${id.name}`,
    severity: t.sev,
  }));
}

// Aggregates
export const totals = {
  identities: identities.length,
  critical: identities.filter((i) => i.riskLevel === "Critical").length,
  high: identities.filter((i) => i.riskLevel === "High").length,
  offboardingGaps: findings.filter((f) => f.type === "OFFBOARDING_GAP").length,
  admins: identities.filter((i) =>
    i.platformAccess.some((p) => p.role === "Administrator" || p.role === "Owner"),
  ).length,
};

export const riskDistribution = (["Critical", "High", "Medium", "Low"] as RiskLevel[]).map(
  (level) => ({
    name: level,
    value: identities.filter((i) => i.riskLevel === level).length,
  }),
);

export const platformDistribution = platforms.map((p) => ({
  name: p,
  value: identities.filter((i) => i.platforms.includes(p)).length,
}));

export const topRiskCategories = findingTypes.map((t) => ({
  name: t.replace(/_/g, " "),
  value: findings.filter((f) => f.type === t).length,
}));

export const departmentRisk = departments.map((d) => ({
  name: d,
  value: Math.round(
    identities.filter((i) => i.department === d).reduce((s, i) => s + i.riskScore, 0) /
      Math.max(1, identities.filter((i) => i.department === d).length),
  ),
}));

export function getIdentity(id: string) {
  return identities.find((i) => i.id === id);
}
export function getFindingsForIdentity(id: string) {
  return findings.filter((f) => f.identityId === id);
}
export function aiAnalysisFor(identity: Identity) {
  return {
    summary: `${identity.name} presents an ${identity.riskLevel.toLowerCase()} identity risk profile driven by ${identity.findingCount} active findings across ${identity.platforms.length} enterprise platforms. The correlation engine has linked behavioral anomalies in cloud access to potential offboarding and privilege management gaps.`,
    impact: `If exploited, this identity could provide an adversary with persistent administrative control across ${identity.platforms.join(", ")}. Blast radius includes production cloud workloads, financial systems, and customer data stores.`,
    explanation: `The risk score of ${identity.riskScore} reflects compound exposure: elevated cross-platform privileges, recent anomalous authentication patterns, and reconciliation drift between the authoritative identity provider and downstream systems. Peer baseline for the ${identity.department} department sits at a median score of 34.`,
    actions: [
      "Initiate just-in-time privilege downgrade for non-essential platforms",
      "Force credential rotation and re-enroll MFA factors",
      "Escalate to IAM team for offboarding reconciliation review",
      "Open ticket for SOC investigation of recent token activity",
    ],
    notes:
      "AI correlation confidence: 94%. Recommendation generated using Identity Graph v3.1 with the most recent 30 days of telemetry across all connected platforms.",
  };
}
