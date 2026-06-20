import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/lib/models";

const styles: Record<RiskLevel, string> = {
  Critical:
    "bg-[color-mix(in_oklab,var(--risk-critical)_18%,transparent)] text-[var(--risk-critical)] ring-[color-mix(in_oklab,var(--risk-critical)_35%,transparent)]",
  High: "bg-[color-mix(in_oklab,var(--risk-high)_15%,transparent)] text-[var(--risk-high)] ring-[color-mix(in_oklab,var(--risk-high)_35%,transparent)]",
  Medium:
    "bg-[color-mix(in_oklab,var(--risk-medium)_12%,transparent)] text-[var(--risk-medium)] ring-[color-mix(in_oklab,var(--risk-medium)_30%,transparent)]",
  Low: "bg-[color-mix(in_oklab,var(--risk-low)_15%,transparent)] text-[var(--risk-low)] ring-[color-mix(in_oklab,var(--risk-low)_35%,transparent)]",
  Informational:
    "bg-[color-mix(in_oklab,var(--risk-info)_15%,transparent)] text-[var(--risk-info)] ring-[color-mix(in_oklab,var(--risk-info)_35%,transparent)]",
};

export function RiskBadge({ level, className }: { level: RiskLevel; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset tabular-nums",
        styles[level],
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current" />
      {level}
    </span>
  );
}

export function RiskScore({ score }: { score: number }) {
  const color =
    score >= 90
      ? "var(--risk-critical)"
      : score >= 70
        ? "var(--risk-high)"
        : score >= 40
          ? "var(--risk-medium)"
          : "var(--risk-low)";
  return (
    <div className="flex items-center gap-2 min-w-[110px]">
      <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="text-sm tabular-nums font-medium w-7 text-right" style={{ color }}>
        {score}
      </span>
    </div>
  );
}

export function PlatformChip({ platform }: { platform: string }) {
  return (
    <span className="inline-flex items-center rounded border border-border bg-muted/50 px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground">
      {platform}
    </span>
  );
}

const confidenceStyles = {
  likely_false_positive_pending_review:
    "bg-[color-mix(in_oklab,var(--risk-low)_15%,transparent)] text-[var(--risk-low)] ring-[color-mix(in_oklab,var(--risk-low)_35%,transparent)]",
  likely_true_positive:
    "bg-[color-mix(in_oklab,var(--risk-critical)_15%,transparent)] text-[var(--risk-critical)] ring-[color-mix(in_oklab,var(--risk-critical)_35%,transparent)]",
} as const;

const confidenceLabels = {
  likely_false_positive_pending_review: "Likely False Positive",
  likely_true_positive: "Confirmed Risk",
} as const;

export function AIConfidenceBadge({
  label,
  className,
}: {
  label: keyof typeof confidenceStyles;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset tabular-nums",
        confidenceStyles[label],
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current" />
      {confidenceLabels[label]}
    </span>
  );
}
