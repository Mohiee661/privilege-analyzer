import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Props {
  label: string;
  value: string | number;
  delta?: string;
  trend?: "up" | "down" | "neutral";
  hint?: string;
  accent?: "critical" | "high" | "primary" | "info" | "default";
  icon?: ReactNode;
}

const accentClasses: Record<NonNullable<Props["accent"]>, string> = {
  critical: "text-[var(--risk-critical)]",
  high: "text-[var(--risk-high)]",
  primary: "text-[var(--primary)]",
  info: "text-[var(--risk-info)]",
  default: "text-foreground",
};

export function MetricCard({
  label,
  value,
  delta,
  trend = "neutral",
  hint,
  accent = "default",
  icon,
}: Props) {
  const TrendIcon = trend === "down" ? ArrowDownRight : ArrowUpRight;
  const trendColor =
    trend === "up"
      ? "text-[var(--risk-critical)]"
      : trend === "down"
        ? "text-[var(--risk-low)]"
        : "text-muted-foreground";
  return (
    <div className="group relative rounded-lg border border-border bg-card p-4 hover:border-[color-mix(in_oklab,var(--primary)_25%,var(--border))] transition-colors">
      <div className="flex items-start justify-between">
        <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </div>
        {icon && <div className="text-muted-foreground/70">{icon}</div>}
      </div>
      <div
        className={cn(
          "mt-3 text-3xl font-semibold tabular-nums tracking-tight",
          accentClasses[accent],
        )}
      >
        {value}
      </div>
      <div className="mt-2 flex items-center gap-2 text-xs">
        {delta && (
          <span className={cn("inline-flex items-center gap-0.5", trendColor)}>
            <TrendIcon className="size-3" />
            {delta}
          </span>
        )}
        {hint && <span className="text-muted-foreground">{hint}</span>}
      </div>
    </div>
  );
}
