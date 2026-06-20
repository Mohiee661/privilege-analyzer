import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { ArrowLeft, Brain, ChevronRight, Clock, Shield, Sparkles } from "lucide-react";
import { PlatformChip, RiskBadge, RiskScore } from "@/components/risk-badge";
import { loadIdentityDetailPageData } from "@/lib/api";

export const Route = createFileRoute("/identity/$id")({
  head: ({ params }) => ({ meta: [{ title: `${params.id} · Identity · IRIP` }] }),
  loader: async ({ params }) => {
    const result = await loadIdentityDetailPageData(params.id);
    if (!result) throw notFound();
    return result;
  },
  notFoundComponent: () => (
    <div className="p-10 text-center text-muted-foreground">Identity not found.</div>
  ),
  component: IdentityDetail,
});

function IdentityDetail() {
  const { identity, findings, timeline, aiAnalysis } = Route.useLoaderData();

  return (
    <div className="mx-auto max-w-[1600px] space-y-6 p-6">
      <Link
        to="/risk-center"
        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-3.5" /> Back to Risk Center
      </Link>

      <header className="rounded-lg border border-border bg-card p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex size-14 items-center justify-center rounded-lg bg-secondary text-lg font-semibold text-secondary-foreground">
              {identity.name
                .split(" ")
                .map((part) => part[0])
                .join("")
                .slice(0, 2)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-semibold tracking-tight">{identity.name}</h1>
                <RiskBadge level={identity.riskLevel} />
              </div>
              <div className="mt-1 text-sm text-muted-foreground">{identity.email}</div>
              <div className="mt-1 text-xs text-muted-foreground">
                {identity.title} · {identity.department} · Status:{" "}
                <span className="text-foreground">{identity.status}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6 text-right">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Risk Score
              </div>
              <div className="mt-1 w-40">
                <RiskScore score={identity.riskScore} />
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Platforms
              </div>
              <div className="mt-1 text-2xl font-semibold tabular-nums">
                {identity.platforms.length}
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Findings
              </div>
              <div className="mt-1 text-2xl font-semibold tabular-nums text-[var(--risk-high)]">
                {findings.length}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <button className="h-9 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground hover:bg-primary/90">
                Initiate remediation
              </button>
              <button className="h-9 rounded-md border border-border bg-card px-3 text-sm text-muted-foreground hover:text-foreground">
                Escalate to SOC
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <section className="rounded-lg border border-border bg-card xl:col-span-2">
          <header className="flex items-center gap-2 border-b border-border px-4 py-3">
            <Shield className="size-4 text-primary" />
            <h3 className="text-sm font-semibold">Platform Access Matrix</h3>
          </header>
          <table className="w-full text-sm">
            <thead className="text-xs uppercase tracking-wider text-muted-foreground">
              <tr className="border-b border-border">
                <th className="px-4 py-2.5 text-left font-medium">Platform</th>
                <th className="px-4 py-2.5 text-left font-medium">Status</th>
                <th className="px-4 py-2.5 text-left font-medium">Role</th>
                <th className="px-4 py-2.5 text-left font-medium">Last Login</th>
              </tr>
            </thead>
            <tbody>
              {identity.platformAccess.map((platformAccess) => (
                <tr key={platformAccess.platform} className="border-b border-border last:border-0">
                  <td className="px-4 py-3">
                    <PlatformChip platform={platformAccess.platform} />
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center gap-1.5 text-xs ${
                        platformAccess.status === "Active"
                          ? "text-[var(--risk-low)]"
                          : "text-[var(--risk-critical)]"
                      }`}
                    >
                      <span className="size-1.5 rounded-full bg-current" /> {platformAccess.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        platformAccess.role === "Administrator" ||
                        platformAccess.role === "Owner" ||
                        platformAccess.role === "Global Administrator"
                          ? "font-medium text-[var(--risk-high)]"
                          : "text-foreground"
                      }
                    >
                      {platformAccess.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {new Date(platformAccess.lastLogin).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="rounded-lg border border-border bg-card">
          <header className="flex items-center gap-2 border-b border-border px-4 py-3">
            <Clock className="size-4 text-primary" />
            <h3 className="text-sm font-semibold">Risk Timeline</h3>
          </header>
          <ol className="relative space-y-4 p-4 before:absolute before:bottom-6 before:left-6 before:top-6 before:w-px before:bg-border">
            {timeline.map((event) => (
              <li key={event.id} className="relative flex gap-3">
                <div
                  className="relative z-10 mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-card ring-2"
                  style={{
                    // @ts-expect-error custom ring variable
                    "--tw-ring-color":
                      event.severity === "Critical"
                        ? "#E54D2E"
                        : event.severity === "High"
                          ? "#F59E0B"
                          : event.severity === "Medium"
                            ? "#FFE0C2"
                            : "#60A5FA",
                  }}
                >
                  <span
                    className="size-2 rounded-full"
                    style={{
                      background:
                        event.severity === "Critical"
                          ? "#E54D2E"
                          : event.severity === "High"
                            ? "#F59E0B"
                            : event.severity === "Medium"
                              ? "#FFE0C2"
                              : "#60A5FA",
                    }}
                  />
                </div>
                <div className="min-w-0 flex-1 pb-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-medium text-foreground">{event.type}</div>
                    <PlatformChip platform={event.platform} />
                  </div>
                  <div className="mt-0.5 text-xs text-muted-foreground">{event.description}</div>
                  <div className="mt-1 text-[11px] text-muted-foreground/70">
                    {new Date(event.timestamp).toLocaleString()}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </section>
      </div>

      <section className="rounded-lg border border-border bg-card">
        <header className="flex items-center justify-between border-b border-border px-4 py-3">
          <h3 className="text-sm font-semibold">Active Findings ({findings.length})</h3>
          <Link
            to="/findings"
            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            View all <ChevronRight className="size-3" />
          </Link>
        </header>
        <div className="divide-y divide-border">
          {findings.length === 0 && (
            <div className="p-6 text-center text-sm text-muted-foreground">No active findings.</div>
          )}
          {findings.map((finding) => (
            <div key={finding.id} className="p-4 hover:bg-muted/30">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <code className="rounded bg-muted px-1.5 py-0.5 text-[11px] font-medium text-primary">
                      {finding.type}
                    </code>
                    <RiskBadge level={finding.severity} />
                  </div>
                  <div className="mt-2 text-sm text-foreground">{finding.description}</div>
                  <div className="mt-2 grid grid-cols-1 gap-3 text-xs md:grid-cols-2">
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                        Evidence
                      </div>
                      <div className="mt-1 text-foreground/90">{finding.evidence}</div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                        Recommendation
                      </div>
                      <div className="mt-1 text-foreground/90">{finding.recommendation}</div>
                    </div>
                  </div>
                </div>
                <div className="shrink-0 flex flex-col gap-1">
                  {finding.platforms.map((platform) => (
                    <PlatformChip key={platform} platform={platform} />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-[color-mix(in_oklab,var(--primary)_20%,var(--border))] bg-gradient-to-b from-[color-mix(in_oklab,var(--primary)_4%,var(--card))] to-card">
        <header className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="flex size-7 items-center justify-center rounded-md bg-primary/15">
              <Sparkles className="size-3.5 text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-semibold">AI Security Analysis</h3>
              <p className="text-[11px] text-muted-foreground">
                Identity Graph v3.1 · {new Date().toLocaleString()}
              </p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <Brain className="size-3" /> Confidence 94%
          </span>
        </header>
        <div className="grid grid-cols-1 gap-4 p-5 lg:grid-cols-2">
          <AIBlock title="Executive Summary" body={aiAnalysis.summary} />
          <AIBlock title="Security Impact" body={aiAnalysis.impact} />
          <AIBlock title="Risk Explanation" body={aiAnalysis.explanation} />
          <div>
            <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Recommended Actions
            </div>
            <ul className="mt-2 space-y-1.5">
              {aiAnalysis.actions.map((action, index) => (
                <li key={index} className="flex items-start gap-2 text-sm">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                  <span className="text-foreground/90">{action}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <footer className="border-t border-border bg-muted/20 px-5 py-3 text-xs text-muted-foreground">
          <span className="font-medium text-foreground">Analyst notes:</span> {aiAnalysis.notes}
        </footer>
      </section>
    </div>
  );
}

function AIBlock({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
        {title}
      </div>
      <p className="mt-2 text-sm leading-relaxed text-foreground/90">{body}</p>
    </div>
  );
}
