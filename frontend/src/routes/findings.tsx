import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { EmptyState, PageErrorState, PageLoadingState } from "@/components/page-state";
import { PlatformChip, RiskBadge } from "@/components/risk-badge";
import { loadFindingsPageData } from "@/services/findings";
import { findingTypeLabel } from "@/lib/api";
import type { FindingType } from "@/lib/models";

export const Route = createFileRoute("/findings")({
  head: () => ({ meta: [{ title: "Findings · IRIP" }] }),
  loader: loadFindingsPageData,
  pendingComponent: () => <PageLoadingState title="Loading findings" />,
  errorComponent: () => (
    <PageErrorState title="Backend unavailable" message="Unable to load findings." />
  ),
  component: Findings,
});

const categories: (FindingType | "All")[] = [
  "All",
  "OFFBOARDING_GAP",
  "MULTI_PLATFORM_ADMIN",
  "STALE_ACTIVE_ACCOUNT",
  "SUSPENDED_ACCOUNT_MISMATCH",
  "EXCESSIVE_PLATFORM_EXPOSURE",
  "HIDDEN_PRIVILEGE_VIA_GROUP_NESTING",
  "UNAPPROVED_PRIVILEGE_SPIKE",
  "STALE_OR_MISUSED_TOKEN",
];

function Findings() {
  const data = Route.useLoaderData();
  const [category, setCategory] = useState<(typeof categories)[number]>("All");
  const list = data.findings
    .filter((finding) => category === "All" || finding.type === category)
    .slice(0, 60);

  return (
    <div className="mx-auto max-w-[1600px] space-y-4 p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Findings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          All identity risk findings across the organization · {data.findings.length} total
        </p>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {categories.map((item) => (
          <button
            key={item}
            onClick={() => setCategory(item)}
                  className={`rounded-md border px-2.5 py-1.5 text-xs font-medium transition-colors ${
              category === item
                ? "border-primary/30 bg-primary/10 text-primary"
                : "border-border bg-card text-muted-foreground hover:text-foreground"
            }`}
          >
            {item === "All" ? "All" : findingTypeLabel(item)}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {list.length === 0 && (
          <div className="lg:col-span-2">
            <EmptyState
              title="No findings available"
              message="Try selecting a different category or check backend data."
            />
          </div>
        )}
        {list.map((finding) => {
          const identity = data.identityById[finding.identityId];
          return (
            <div
              key={finding.id}
              className="rounded-lg border border-border bg-card p-4 hover:border-[color-mix(in_oklab,var(--primary)_25%,var(--border))]"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <code className="rounded bg-muted px-1.5 py-0.5 text-[11px] font-medium text-primary">
                    {findingTypeLabel(finding.type)}
                  </code>
                  <RiskBadge level={finding.severity} />
                </div>
                <div className="flex flex-wrap gap-1">
                  {finding.platforms.map((platform) => (
                    <PlatformChip key={platform} platform={platform} />
                  ))}
                </div>
              </div>
              {identity && (
                <Link
                  to="/identity/$id"
                  params={{ id: identity.id }}
                  className="mt-3 inline-flex items-center gap-2 group"
                >
                  <div className="flex size-6 items-center justify-center rounded bg-secondary text-[10px] font-semibold text-secondary-foreground">
                    {identity.name
                      .split(" ")
                      .map((part) => part[0])
                      .join("")
                      .slice(0, 2)}
                  </div>
                  <div className="text-sm font-medium group-hover:text-primary">
                    {identity.name}
                  </div>
                  <span className="text-xs text-muted-foreground">· {identity.department}</span>
                </Link>
              )}
              <p className="mt-3 text-sm text-foreground/90">{finding.description}</p>
              <div className="mt-3 rounded-md border border-border bg-muted/30 p-3 text-xs">
                <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  Recommended action
                </div>
                <div className="mt-1 text-foreground/90">{finding.recommendation}</div>
              </div>
              <div className="mt-3 rounded-md border border-border bg-background/80 p-3 text-xs text-muted-foreground">
                <div className="text-[10px] font-medium uppercase tracking-wider">Evidence</div>
                <div className="mt-1 text-foreground/90">{finding.evidence}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
