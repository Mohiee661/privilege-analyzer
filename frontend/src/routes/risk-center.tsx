import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import {
  ChevronDown,
  Download,
  Filter,
  MoreHorizontal,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { PlatformChip, RiskBadge, RiskScore } from "@/components/risk-badge";
import { loadRiskCenterPageData } from "@/lib/api";
import type { Identity, RiskLevel } from "@/lib/models";

export const Route = createFileRoute("/risk-center")({
  head: () => ({ meta: [{ title: "Risk Center · IRIP" }] }),
  loader: loadRiskCenterPageData,
  component: RiskCenter,
});

const LEVELS: RiskLevel[] = ["Critical", "High", "Medium", "Low", "Informational"];

function RiskCenter() {
  const data = Route.useLoaderData();
  const [q, setQ] = useState("");
  const [level, setLevel] = useState<RiskLevel | "All">("All");
  const [platform, setPlatform] = useState<string>("All");
  const [dept, setDept] = useState<string>("All");
  const [sortDesc, setSortDesc] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const departments = useMemo(
    () => ["All", ...new Set(data.identities.map((identity) => identity.department))],
    [data.identities],
  );
  const platforms = ["All", "AD", "Azure", "AWS", "Okta", "Salesforce"];

  const filtered = useMemo(() => {
    const filteredList = data.identities.filter((identity) => {
      if (q && !`${identity.name} ${identity.email}`.toLowerCase().includes(q.toLowerCase()))
        return false;
      if (level !== "All" && identity.riskLevel !== level) return false;
      if (
        platform !== "All" &&
        !identity.platforms.includes(platform as Identity["platforms"][number])
      ) {
        return false;
      }
      if (dept !== "All" && identity.department !== dept) return false;
      return true;
    });
    return filteredList.sort((a, b) =>
      sortDesc ? b.riskScore - a.riskScore : a.riskScore - b.riskScore,
    );
  }, [q, level, platform, dept, sortDesc, data.identities]);

  const toggle = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelected(next);
  };

  return (
    <div className="mx-auto max-w-[1600px] space-y-4 p-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Risk Center</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Security analyst investigation workspace · {filtered.length} identities
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="inline-flex h-9 items-center gap-1.5 rounded-md border border-border bg-card px-3 text-sm text-muted-foreground hover:text-foreground">
            <Download className="size-4" /> Export
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card">
        <div className="flex flex-wrap items-center gap-2 border-b border-border p-3">
          <div className="relative min-w-[240px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Filter by name or email..."
              className="h-9 w-full rounded-md border border-border bg-background pl-9 pr-3 text-sm placeholder:text-muted-foreground/70 focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
          <FilterSelect
            label="Risk"
            value={level}
            onChange={(value) => setLevel(value as RiskLevel | "All")}
            options={["All", ...LEVELS]}
          />
          <FilterSelect
            label="Platform"
            value={platform}
            onChange={setPlatform}
            options={platforms}
          />
          <FilterSelect label="Department" value={dept} onChange={setDept} options={departments} />
          <button className="inline-flex h-9 items-center gap-1.5 rounded-md border border-border bg-background px-3 text-sm text-muted-foreground hover:text-foreground">
            <SlidersHorizontal className="size-3.5" /> Columns
          </button>
          <button className="inline-flex h-9 items-center gap-1.5 rounded-md border border-border bg-background px-3 text-sm text-muted-foreground hover:text-foreground">
            <Filter className="size-3.5" /> More filters
          </button>
        </div>

        {selected.size > 0 && (
          <div className="flex items-center gap-3 border-b border-border bg-secondary/30 px-4 py-2 text-xs">
            <span className="font-medium text-primary">{selected.size} selected</span>
            <button className="text-muted-foreground hover:text-foreground">
              Assign to analyst
            </button>
            <button className="text-muted-foreground hover:text-foreground">Mark reviewed</button>
            <button className="text-[var(--risk-critical)] hover:underline">Escalate</button>
          </div>
        )}

        <div className="overflow-x-auto scrollbar-thin">
          <table className="min-w-[1100px] w-full text-sm">
            <thead className="bg-muted/30 text-xs uppercase tracking-wider text-muted-foreground">
              <tr className="border-b border-border">
                <th className="w-10 px-4 py-2.5">
                  <input
                    type="checkbox"
                    checked={selected.size === filtered.length && filtered.length > 0}
                    onChange={() =>
                      setSelected(
                        selected.size === filtered.length
                          ? new Set()
                          : new Set(filtered.map((identity) => identity.id)),
                      )
                    }
                    className="accent-[var(--primary)]"
                  />
                </th>
                <th className="px-4 py-2.5 text-left font-medium">Identity</th>
                <th className="px-4 py-2.5 text-left font-medium">Email</th>
                <th
                  className="cursor-pointer px-4 py-2.5 text-left font-medium"
                  onClick={() => setSortDesc(!sortDesc)}
                >
                  <span className="inline-flex items-center gap-1">
                    Risk Score{" "}
                    <ChevronDown
                      className={`size-3 transition-transform ${sortDesc ? "" : "rotate-180"}`}
                    />
                  </span>
                </th>
                <th className="px-4 py-2.5 text-left font-medium">Level</th>
                <th className="px-4 py-2.5 text-left font-medium">Platforms</th>
                <th className="px-4 py-2.5 text-left font-medium">Findings</th>
                <th className="px-4 py-2.5 text-left font-medium">Last Login</th>
                <th className="px-4 py-2.5 text-left font-medium">Department</th>
                <th className="px-4 py-2.5 text-left font-medium">Status</th>
                <th className="w-10 px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 50).map((identity) => (
                <tr
                  key={identity.id}
                  className="group border-b border-border last:border-0 hover:bg-muted/30"
                >
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selected.has(identity.id)}
                      onChange={() => toggle(identity.id)}
                      className="accent-[var(--primary)]"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <Link to="/identity/$id" params={{ id: identity.id }} className="block">
                      <div className="flex items-center gap-2.5">
                        <div className="flex size-7 items-center justify-center rounded bg-secondary text-[10px] font-semibold text-secondary-foreground">
                          {identity.name
                            .split(" ")
                            .map((part) => part[0])
                            .join("")
                            .slice(0, 2)}
                        </div>
                        <div>
                          <div className="font-medium text-foreground group-hover:text-primary">
                            {identity.name}
                          </div>
                          <div className="text-xs text-muted-foreground">{identity.title}</div>
                        </div>
                      </div>
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{identity.email}</td>
                  <td className="px-4 py-3">
                    <RiskScore score={identity.riskScore} />
                  </td>
                  <td className="px-4 py-3">
                    <RiskBadge level={identity.riskLevel} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {identity.platforms.map((platformName) => (
                        <PlatformChip key={platformName} platform={platformName} />
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 tabular-nums text-muted-foreground">
                    {identity.findingCount}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {new Date(identity.lastLogin).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{identity.department}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs ${
                        identity.status === "Active"
                          ? "text-[var(--risk-low)]"
                          : identity.status === "Offboarded"
                            ? "text-[var(--risk-critical)]"
                            : "text-[var(--risk-high)]"
                      }`}
                    >
                      {identity.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <MoreHorizontal className="size-4 text-muted-foreground" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-muted-foreground">
          <div>
            Showing {Math.min(50, filtered.length)} of {filtered.length}
          </div>
          <div className="flex items-center gap-1">
            <button className="rounded border border-border px-2 py-1 hover:text-foreground">
              Previous
            </button>
            <button className="rounded border border-border bg-muted px-2 py-1 text-foreground">
              1
            </button>
            <button className="rounded border border-border px-2 py-1 hover:text-foreground">
              2
            </button>
            <button className="rounded border border-border px-2 py-1 hover:text-foreground">
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <label className="inline-flex h-9 items-center gap-1.5 rounded-md border border-border bg-background px-2.5 text-sm text-muted-foreground">
      <span className="text-xs">{label}:</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-transparent text-sm text-foreground focus:outline-none"
      >
        {options.map((option) => (
          <option key={option} value={option} className="bg-card">
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
