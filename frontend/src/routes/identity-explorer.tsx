import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Search } from "lucide-react";
import { EmptyState, PageErrorState, PageLoadingState } from "@/components/page-state";
import { PlatformChip, RiskBadge } from "@/components/risk-badge";
import { loadIdentityExplorerPageData } from "@/services/identities";

export const Route = createFileRoute("/identity-explorer")({
  head: () => ({ meta: [{ title: "Identity Explorer · IRIP" }] }),
  loader: loadIdentityExplorerPageData,
  pendingComponent: () => <PageLoadingState title="Loading identities" />,
  errorComponent: () => (
    <PageErrorState title="Backend unavailable" message="Unable to load identities." />
  ),
  component: Explorer,
});

function Explorer() {
  const data = Route.useLoaderData();
  const [q, setQ] = useState("");
  const list = data.identities.filter((identity) =>
    `${identity.name} ${identity.email} ${identity.department}`
      .toLowerCase()
      .includes(q.toLowerCase()),
  );

  return (
    <div className="mx-auto max-w-[1600px] space-y-4 p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Identity Explorer</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Browse and correlate identities across connected platforms.
        </p>
      </div>

      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={q}
          onChange={(event) => setQ(event.target.value)}
          placeholder="Search by name, email, or department..."
          className="h-10 w-full max-w-xl rounded-md border border-border bg-card pl-9 pr-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {list.length === 0 && (
          <div className="sm:col-span-2 lg:col-span-3 xl:col-span-4">
            <EmptyState
              title="No identities available"
              message="Try a different search term or check the backend data."
            />
          </div>
        )}
        {list.slice(0, 32).map((identity) => (
          <Link
            key={identity.id}
            to="/identity/$id"
            params={{ id: identity.id }}
            className="group rounded-lg border border-border bg-card p-4 transition-colors hover:border-[color-mix(in_oklab,var(--primary)_30%,var(--border))]"
          >
            <div className="flex items-start justify-between">
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-md bg-secondary text-sm font-semibold text-secondary-foreground">
                  {identity.name
                    .split(" ")
                    .map((part) => part[0])
                    .join("")
                    .slice(0, 2)}
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold group-hover:text-primary">
                    {identity.name}
                  </div>
                  <div className="truncate text-xs text-muted-foreground">{identity.email}</div>
                </div>
              </div>
              <RiskBadge level={identity.riskLevel} />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div>
                <div className="text-muted-foreground">Department</div>
                <div className="mt-0.5 font-medium">{identity.department}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Last login</div>
                <div className="mt-0.5 font-medium">
                  {new Date(identity.lastLogin).toLocaleDateString()}
                </div>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-1">
              {identity.platforms.map((platform) => (
                <PlatformChip key={platform} platform={platform} />
              ))}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
