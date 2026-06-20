import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Brain, Clock, Search, Send, Sparkles } from "lucide-react";
import { EmptyState, PageErrorState, PageLoadingState } from "@/components/page-state";
import { PlatformChip, RiskBadge } from "@/components/risk-badge";
import { loadCopilotPageData } from "@/services/reports";

export const Route = createFileRoute("/ai-copilot")({
  head: () => ({ meta: [{ title: "AI Copilot · IRIP" }] }),
  loader: loadCopilotPageData,
  pendingComponent: () => <PageLoadingState title="Loading copilot" />,
  errorComponent: () => (
    <PageErrorState title="Backend unavailable" message="Unable to load AI reports." />
  ),
  component: Copilot,
});

function Copilot() {
  const data = Route.useLoaderData();
  const critical = [...data.topCritical].sort((a, b) => b.riskScore - a.riskScore).slice(0, 8);
  const [selectedId, setSelectedId] = useState(critical[0]?.id ?? data.identities[0]?.id ?? "");
  if (critical.length === 0 || data.identities.length === 0) {
    return (
      <div className="mx-auto max-w-[1600px] p-6">
        <EmptyState
          title="No identities available"
          message="The backend returned no identities to investigate."
        />
      </div>
    );
  }
  const identity = data.identityById[selectedId] ?? critical[0] ?? data.identities[0];
  const findings = data.findingsByIdentityId[selectedId] ?? [];
  const aiReport = data.aiReportById[selectedId];
  const ai = aiReport
    ? {
        summary: aiReport.summary,
        impact: aiReport.securityImpact,
        explanation: `Risk score ${aiReport.riskScore} is driven by ${findings.length} linked findings across ${identity.platforms.length} platforms.`,
        actions: aiReport.recommendedActions,
        notes: "AI insight sourced from backend copilot export.",
      }
    : {
        summary: `${identity.name} presents a ${identity.riskLevel.toLowerCase()} identity risk profile driven by ${identity.findingCount} active findings across ${identity.platforms.length} enterprise platforms.`,
        impact: `If exploited, this identity could provide an adversary with persistent access across ${identity.platforms.join(", ")}.`,
        explanation: `The risk score of ${identity.riskScore} reflects compound exposure from correlated findings and platform access.`,
        actions: [
          "Review standing access across connected platforms",
          "Rotate credentials and confirm MFA coverage",
          "Escalate for offboarding or privilege review",
          "Inspect recent login activity for anomalies",
        ],
        notes: "Fallback narrative generated locally because the backend AI report is unavailable.",
      };
  const recent = critical.slice(0, 4);

  return (
    <div className="mx-auto max-w-[1600px] p-6">
      <div className="mb-4">
        <h1 className="text-2xl font-semibold tracking-tight">AI Copilot</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Security investigation assistant powered by backend AI reports.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-4">
          <div className="rounded-lg border border-border bg-card">
            <div className="border-b border-border p-3">
              <div className="relative">
                <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <input
                  placeholder="Search identity..."
                  className="h-8 w-full rounded-md border border-border bg-background pl-8 pr-2 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
            </div>
            <div>
              <div className="px-3 pb-1 pt-3 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                Critical Users
              </div>
              <ul>
                {critical.map((item) => (
                  <li key={item.id}>
                    <button
                      onClick={() => setSelectedId(item.id)}
                      className={`flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-muted/40 ${
                        selectedId === item.id ? "border-l-2 border-primary bg-muted/50" : ""
                      }`}
                    >
                      <div className="flex size-7 items-center justify-center rounded bg-secondary text-[10px] font-semibold text-secondary-foreground">
                        {item.name
                          .split(" ")
                          .map((part) => part[0])
                          .join("")
                          .slice(0, 2)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-xs font-medium">{item.name}</div>
                        <div className="truncate text-[10px] text-muted-foreground">
                          {item.department}
                        </div>
                      </div>
                      <span
                        className="text-xs font-medium tabular-nums"
                        style={{
                          color:
                            item.riskScore >= 90
                              ? "#E54D2E"
                              : item.riskScore >= 70
                                ? "#F59E0B"
                                : "#FFE0C2",
                        }}
                      >
                        {item.riskScore}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card p-3">
            <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Recent Investigations
            </div>
            <ul className="mt-2 space-y-1.5">
              {recent.map((item) => (
                <li key={item.id} className="flex items-center gap-2 text-xs">
                  <Clock className="size-3 text-muted-foreground" />
                  <span className="flex-1 truncate">{item.name}</span>
                  <span className="text-muted-foreground">2h</span>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        <section className="space-y-4">
          <div className="rounded-lg border border-[color-mix(in_oklab,var(--primary)_20%,var(--border))] bg-gradient-to-b from-[color-mix(in_oklab,var(--primary)_5%,var(--card))] to-card">
            <header className="flex items-center justify-between border-b border-border px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="flex size-7 items-center justify-center rounded-md bg-primary/15">
                  <Sparkles className="size-3.5 text-primary" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold">AI Investigation Summary</h3>
                  <p className="text-[11px] text-muted-foreground">
                    Subject: {identity.name} · {identity.email}
                  </p>
                </div>
              </div>
              <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
                <Brain className="size-3" /> Confidence 94%
              </span>
            </header>
            <div className="space-y-4 p-5">
              <div>
                <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  Summary
                </div>
                <p className="mt-2 text-sm leading-relaxed text-foreground/90">{ai.summary}</p>
              </div>
              <div>
                <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  Security Impact
                </div>
                <p className="mt-2 text-sm leading-relaxed text-foreground/90">{ai.impact}</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-border bg-card p-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold">Recommended Actions</h4>
                <RiskBadge level={identity.riskLevel} />
              </div>
              <ul className="mt-3 space-y-2">
                {ai.actions.map((action, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 rounded-md border border-border bg-muted/20 p-2.5 text-sm"
                  >
                    <span className="mt-1 inline-flex size-5 shrink-0 items-center justify-center rounded bg-primary/15 text-[10px] font-semibold text-primary tabular-nums">
                      {index + 1}
                    </span>
                    <span className="text-foreground/90">{action}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-lg border border-border bg-card p-4">
              <h4 className="text-sm font-semibold">Risk Evidence</h4>
              <ul className="mt-3 space-y-2 text-sm">
                <li className="flex justify-between border-b border-border pb-2">
                  <span className="text-muted-foreground">Cross-platform admin</span>
                  <span className="font-medium text-[var(--risk-high)]">
                    {findings.some((finding) => finding.type === "MULTI_PLATFORM_ADMIN")
                      ? "Confirmed"
                      : "Review"}
                  </span>
                </li>
                <li className="flex justify-between border-b border-border pb-2">
                  <span className="text-muted-foreground">Stale session detected</span>
                  <span className="font-medium">
                    {Math.max(1, Math.floor(identity.riskScore / 5))}d ago
                  </span>
                </li>
                <li className="flex justify-between border-b border-border pb-2">
                  <span className="text-muted-foreground">Status drift</span>
                  <span className="font-medium text-[var(--risk-critical)]">
                    {findings.length > 0 ? "Present" : "None"}
                  </span>
                </li>
                <li className="flex justify-between">
                  <span className="text-muted-foreground">Platforms</span>
                  <span className="flex gap-1">
                    {identity.platforms.map((platform) => (
                      <PlatformChip key={platform} platform={platform} />
                    ))}
                  </span>
                </li>
              </ul>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card p-3">
            <div className="flex items-center gap-2">
              <input
                placeholder="Ask Copilot: 'Why is this identity high risk?'"
                className="h-10 flex-1 rounded-md border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              />
              <button className="inline-flex h-10 items-center gap-1.5 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90">
                <Send className="size-3.5" /> Investigate
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
