import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  ShieldAlert,
  Users,
  FileWarning,
  Sparkles,
  FileBarChart,
  Settings,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/risk-center", label: "Risk Center", icon: ShieldAlert },
  { to: "/identity-explorer", label: "Identity Explorer", icon: Users },
  { to: "/findings", label: "Findings", icon: FileWarning },
  { to: "/ai-copilot", label: "AI Copilot", icon: Sparkles },
  { to: "/reports", label: "Reports", icon: FileBarChart },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

export function AppSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <aside className="hidden md:flex w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar">
      <div className="flex h-14 items-center gap-2 px-4 border-b border-sidebar-border">
        <div className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <ShieldCheck className="size-4" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold text-sidebar-foreground">IRIP</span>
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
            Identity Risk Intel
          </span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto p-2 scrollbar-thin">
        <div className="px-2 py-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Workspace
        </div>
        <ul className="space-y-0.5">
          {nav.map((item) => {
            const active = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to);
            const Icon = item.icon;
            return (
              <li key={item.to}>
                <Link
                  to={item.to}
                  className={cn(
                    "group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors",
                    active
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
                  )}
                >
                  <Icon
                    className={cn(
                      "size-4",
                      active ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
                    )}
                  />
                  <span className="font-medium">{item.label}</span>
                  {active && <span className="ml-auto size-1.5 rounded-full bg-primary" />}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="m-2 rounded-md border border-sidebar-border bg-sidebar-accent/40 p-3">
        <div className="flex items-center gap-2">
          <div className="size-2 rounded-full bg-[var(--risk-low)]" />
          <span className="text-xs font-medium text-sidebar-foreground">
            All collectors healthy
          </span>
        </div>
        <div className="mt-1 text-[11px] text-muted-foreground">Last sync · 2 min ago</div>
      </div>
    </aside>
  );
}
