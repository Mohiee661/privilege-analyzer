import type { ReactNode } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  ShieldAlert,
  UserMinus,
  UserCog,
  Users,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { MetricCard } from "@/components/metric-card";
import { PageErrorState, PageLoadingState } from "@/components/page-state";
import { PlatformChip, RiskBadge, RiskScore } from "@/components/risk-badge";
import { loadDashboardPageData } from "@/services/dashboard";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard · IRIP" },
      { name: "description", content: "Executive overview of organizational identity risk." },
    ],
  }),
  loader: loadDashboardPageData,
  pendingComponent: () => <PageLoadingState title="Loading dashboard" />,
  errorComponent: () => (
    <PageErrorState
      title="Backend unavailable"
      message="Unable to load dashboard data from the API."
    />
  ),
  component: Dashboard,
});

const RISK_COLORS: Record<string, string> = {
  Critical: "#E54D2E",
  High: "#F59E0B",
  Medium: "#FFE0C2",
  Low: "#10B981",
  Informational: "#60A5FA",
};

function ChartCard({
  title,
  subtitle,
  children,
  action,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <section className="rounded-lg border border-border bg-card">
      <header className="flex items-center justify-between border-b border-border px-4 py-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          {subtitle && <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>}
        </div>
        {action}
      </header>
      <div className="p-4">{children}</div>
    </section>
  );
}

function Dashboard() {
  const data = Route.useLoaderData();
  const topCritical = data.topCritical;

  return (
    <div className="mx-auto max-w-[1600px] space-y-6 p-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Workspace · Connected APIs
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Identity Risk Overview</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Real-time correlation across {data.dashboard.totalIdentities} identities and 5 connected
            platforms.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="h-9 rounded-md border border-border bg-card px-3 text-sm text-muted-foreground hover:text-foreground">
            Last 7 days
          </button>
          <button className="h-9 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground hover:bg-primary/90">
            Export report
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        <MetricCard
          label="Total Identities"
          value={data.dashboard.totalIdentities}
          delta="Real backend data"
          trend="up"
          hint="from FastAPI"
          icon={<Users className="size-4" />}
        />
        <MetricCard
          label="Critical Risks"
          value={data.dashboard.criticalRisks}
          delta="Live"
          trend="up"
          hint="needs review"
          accent="critical"
          icon={<ShieldAlert className="size-4" />}
        />
        <MetricCard
          label="High Risks"
          value={data.dashboard.highRisks}
          delta="Live"
          trend="up"
          hint="last refresh"
          accent="high"
          icon={<AlertTriangle className="size-4" />}
        />
        <MetricCard
          label="Offboarding Gaps"
          value={data.dashboard.offboardingGaps}
          delta="Live"
          trend="down"
          hint="correlated findings"
          accent="primary"
          icon={<UserMinus className="size-4" />}
        />
        <MetricCard
          label="Admin Accounts"
          value={data.dashboard.adminAccounts}
          delta="Live"
          trend="up"
          hint="cross-platform"
          icon={<UserCog className="size-4" />}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard title="Risk Distribution" subtitle="Identities by risk tier">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.riskDistribution}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  stroke="none"
                >
                  {data.riskDistribution.map((entry) => (
                    <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "#191919",
                    border: "1px solid #201E18",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {data.riskDistribution.map((risk) => (
              <div key={risk.name} className="flex items-center gap-2 text-xs">
                <span
                  className="size-2 rounded-full"
                  style={{ background: RISK_COLORS[risk.name] }}
                />
                <span className="text-muted-foreground">{risk.name}</span>
                <span className="ml-auto tabular-nums font-medium">{risk.value}</span>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Platform Distribution" subtitle="Identity coverage per platform">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.platformDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#201E18" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: "#8a8a8a", fontSize: 11 }}
                  axisLine={{ stroke: "#201E18" }}
                  tickLine={false}
                />
                <YAxis tick={{ fill: "#8a8a8a", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  cursor={{ fill: "#222" }}
                  contentStyle={{
                    background: "#191919",
                    border: "1px solid #201E18",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="value" fill="#FFE0C2" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <ChartCard title="Top Risk Categories" subtitle="Active findings by category">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.topRiskCategories} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#201E18" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fill: "#8a8a8a", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={180}
                  tick={{ fill: "#c8c8c8", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ fill: "#222" }}
                  contentStyle={{
                    background: "#191919",
                    border: "1px solid #201E18",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="value" fill="#F59E0B" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <ChartCard title="Department Risk Exposure" subtitle="Mean risk score per department">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.departmentRisk}>
                <CartesianGrid strokeDasharray="3 3" stroke="#201E18" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: "#8a8a8a", fontSize: 11 }}
                  axisLine={{ stroke: "#201E18" }}
                  tickLine={false}
                />
                <YAxis tick={{ fill: "#8a8a8a", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  cursor={{ fill: "#222" }}
                  contentStyle={{
                    background: "#191919",
                    border: "1px solid #201E18",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {data.departmentRisk.map((department) => (
                    <Cell
                      key={department.name}
                      fill={
                        department.value >= 70
                          ? "#E54D2E"
                          : department.value >= 50
                            ? "#F59E0B"
                            : "#FFE0C2"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </div>

      <section className="rounded-lg border border-border bg-card">
        <header className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <Activity className="size-4 text-[var(--risk-critical)]" />
            <h3 className="text-sm font-semibold">Recent Critical Findings</h3>
          </div>
          <Link
            to="/risk-center"
            className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
          >
            Open Risk Center <ArrowUpRight className="size-3" />
          </Link>
        </header>
        <table className="w-full text-sm">
          <thead className="text-xs uppercase tracking-wider text-muted-foreground">
            <tr className="border-b border-border">
              <th className="px-4 py-2.5 text-left font-medium">Identity</th>
              <th className="w-[180px] px-4 py-2.5 text-left font-medium">Risk Score</th>
              <th className="px-4 py-2.5 text-left font-medium">Finding Type</th>
              <th className="px-4 py-2.5 text-left font-medium">Platforms</th>
              <th className="px-4 py-2.5 text-left font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {topCritical.map((identity) => (
              <tr
                key={identity.id}
                className="border-b border-border last:border-0 hover:bg-muted/40"
              >
                <td className="px-4 py-3">
                  <Link to="/identity/$id" params={{ id: identity.id }} className="block">
                    <div className="font-medium text-foreground">{identity.name}</div>
                    <div className="text-xs text-muted-foreground">{identity.email}</div>
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <RiskScore score={identity.riskScore} />
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-muted-foreground">
                    {data.findingsByIdentityId[identity.id]?.[0]?.type ?? "OFFBOARDING_GAP"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {identity.platforms.map((platform) => (
                      <PlatformChip key={platform} platform={platform} />
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <RiskBadge level={identity.riskLevel} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
