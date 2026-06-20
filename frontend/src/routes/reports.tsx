import type { ReactNode } from "react";
import { createFileRoute } from "@tanstack/react-router";
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
import { Download, FileText } from "lucide-react";
import { PageErrorState, PageLoadingState } from "@/components/page-state";
import { RiskBadge, RiskScore } from "@/components/risk-badge";
import { loadReportsPageData } from "@/services/reports";

export const Route = createFileRoute("/reports")({
  head: () => ({ meta: [{ title: "Reports · IRIP" }] }),
  loader: loadReportsPageData,
  pendingComponent: () => <PageLoadingState title="Loading reports" />,
  errorComponent: () => (
    <PageErrorState title="Backend unavailable" message="Unable to load reports data." />
  ),
  component: Reports,
});

const RISK_COLORS: Record<string, string> = {
  Critical: "#E54D2E",
  High: "#F59E0B",
  Medium: "#FFE0C2",
  Low: "#10B981",
  Informational: "#60A5FA",
};

function Reports() {
  const data = Route.useLoaderData();
  const top = [...data.topCritical].sort((a, b) => b.riskScore - a.riskScore).slice(0, 6);

  return (
    <div className="mx-auto max-w-[1600px] space-y-6 p-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Executive Reports</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Board-ready summaries and exports for stakeholders.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="inline-flex h-9 items-center gap-1.5 rounded-md border border-border bg-card px-3 text-sm hover:border-primary/30">
            <Download className="size-3.5" /> Export PDF
          </button>
          <button className="inline-flex h-9 items-center gap-1.5 rounded-md border border-border bg-card px-3 text-sm hover:border-primary/30">
            <Download className="size-3.5" /> Export CSV
          </button>
          <button className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground hover:bg-primary/90">
            <FileText className="size-3.5" /> Generate Summary
          </button>
        </div>
      </div>

      <section className="rounded-lg border border-border bg-card p-5">
        <h2 className="text-sm font-semibold">Executive Summary</h2>
        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
          As of {new Date().toLocaleDateString()}, IRIP monitors {data.dashboard.totalIdentities}{" "}
          identities across 5 connected enterprise platforms.{" "}
          <span className="font-medium text-foreground">
            {data.dashboard.criticalRisks} critical
          </span>{" "}
          and {data.dashboard.highRisks} high-risk identities require analyst review.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
          {[
            { l: "Total Identities", v: data.dashboard.totalIdentities },
            { l: "Critical Risks", v: data.dashboard.criticalRisks, c: "var(--risk-critical)" },
            { l: "Offboarding Gaps", v: data.dashboard.offboardingGaps, c: "var(--primary)" },
            { l: "Admin Accounts", v: data.dashboard.adminAccounts },
          ].map((metric) => (
            <div key={metric.l} className="rounded-md border border-border bg-muted/20 p-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                {metric.l}
              </div>
              <div
                className="mt-1 text-2xl font-semibold tabular-nums"
                style={{ color: metric.c || "inherit" }}
              >
                {metric.v}
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ReportChart title="Risk Distribution">
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={data.riskDistribution}
                dataKey="value"
                nameKey="name"
                innerRadius={50}
                outerRadius={85}
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
        </ReportChart>
        <ReportChart title="Platform Risk Breakdown">
          <ResponsiveContainer width="100%" height={240}>
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
        </ReportChart>
        <ReportChart title="Department Exposure">
          <ResponsiveContainer width="100%" height={240}>
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
        </ReportChart>
        <ReportChart title="Top Critical Identities">
          <ul className="divide-y divide-border">
            {top.map((identity) => (
              <li key={identity.id} className="flex items-center gap-3 py-2.5">
                <div className="flex size-8 items-center justify-center rounded bg-secondary text-[11px] font-semibold text-secondary-foreground">
                  {identity.name
                    .split(" ")
                    .map((part) => part[0])
                    .join("")
                    .slice(0, 2)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{identity.name}</div>
                  <div className="truncate text-[11px] text-muted-foreground">
                    {identity.department} · {identity.email}
                  </div>
                </div>
                <div className="w-32">
                  <RiskScore score={identity.riskScore} />
                </div>
                <RiskBadge level={identity.riskLevel} />
              </li>
            ))}
          </ul>
        </ReportChart>
      </div>
    </div>
  );
}

function ReportChart({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-border bg-card">
      <header className="border-b border-border px-4 py-3">
        <h3 className="text-sm font-semibold">{title}</h3>
      </header>
      <div className="p-4">{children}</div>
    </section>
  );
}
