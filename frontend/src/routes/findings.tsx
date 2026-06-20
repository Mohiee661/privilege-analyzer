import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { EmptyState, PageErrorState, PageLoadingState } from "@/components/page-state";
import { PlatformChip, RiskBadge } from "@/components/risk-badge";
import { loadFindingsPageData } from "@/services/findings";
import { findingTypeLabel } from "@/lib/api";
import type { FindingType, Incident } from "@/lib/models";

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
  const list = data.incidents
    .filter((incident) => category === "All" || incident.riskTypes.includes(category))
    .slice(0, 60);

  return (
    <div className="mx-auto max-w-[1600px] space-y-4 p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Incidents</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Consolidated risk incidents · {data.incidents.length} incidents from {data.findings.length} findings
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
              title="No incidents available"
              message="Try selecting a different category or check backend data."
            />
          </div>
        )}
        {list.map((incident) => {
          if (incident.type === "department") {
            return (
              <div
                key={incident.incidentId}
                className="rounded-lg border border-border bg-card p-4 hover:border-[color-mix(in_oklab,var(--primary)_25%,var(--border))]"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[11px] font-medium text-primary">
                      DEPARTMENT
                    </span>
                    <RiskBadge level={incident.combinedSeverity} />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                      {incident.personCount} people
                    </span>
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-sm font-medium">{incident.department}</div>
                  <div className="text-xs text-muted-foreground">{incident.description}</div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {incident.riskTypes.map((type) => (
                    <code key={type} className="rounded bg-muted px-1.5 py-0.5 text-[11px] font-medium text-primary">
                      {findingTypeLabel(type)}
                    </code>
                  ))}
                </div>
              </div>
            );
          }

          const identity = incident.personId ? data.identityById[incident.personId] : null;
          return (
            <div
              key={incident.incidentId}
              className="rounded-lg border border-border bg-card p-4 hover:border-[color-mix(in_oklab,var(--primary)_25%,var(--border))]"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                    {incident.findingCount} findings
                  </span>
                  <RiskBadge level={incident.combinedSeverity} />
                </div>
                <div className="flex flex-wrap gap-1">
                  {incident.riskTypes.slice(0, 2).map((type) => (
                    <code key={type} className="rounded bg-muted px-1.5 py-0.5 text-[11px] font-medium text-primary">
                      {findingTypeLabel(type)}
                    </code>
                  ))}
                  {incident.riskTypes.length > 2 && (
                    <span className="rounded bg-muted px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground">
                      +{incident.riskTypes.length - 2}
                    </span>
                  )}
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
              {incident.name && !identity && (
                <div className="mt-3 flex items-center gap-2">
                  <div className="flex size-6 items-center justify-center rounded bg-secondary text-[10px] font-semibold text-secondary-foreground">
                    {incident.name
                      .split(" ")
                      .map((part) => part[0])
                      .join("")
                      .slice(0, 2)}
                  </div>
                  <div className="text-sm font-medium">{incident.name}</div>
                  {incident.department && (
                    <span className="text-xs text-muted-foreground">· {incident.department}</span>
                  )}
                </div>
              )}
              <div className="mt-3 rounded-md border border-border bg-muted/30 p-3 text-xs">
                <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  Consolidated findings
                </div>
                <div className="mt-1 text-foreground/90">
                  {incident.findings.slice(0, 2).map((f) => f.description).join("; ")}
                  {incident.findings.length > 2 && "..."}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
