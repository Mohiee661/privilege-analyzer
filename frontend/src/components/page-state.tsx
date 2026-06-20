import { AlertTriangle, Loader2, WifiOff } from "lucide-react";

export function PageLoadingState({ title = "Loading data" }: { title?: string }) {
  return (
    <div className="mx-auto max-w-[1600px] space-y-4 p-6">
      <div className="space-y-2">
        <div className="h-7 w-64 animate-pulse rounded bg-muted/60" />
        <div className="h-4 w-96 animate-pulse rounded bg-muted/40" />
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              {title}
            </div>
            <div className="mt-4 h-20 animate-pulse rounded bg-muted/30" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function PageErrorState({
  title = "Backend unavailable",
  message = "Unable to load data from the API.",
}: {
  title?: string;
  message?: string;
}) {
  return (
    <div className="mx-auto flex max-w-[960px] items-center justify-center p-10">
      <div className="w-full rounded-lg border border-border bg-card p-6 text-center">
        <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-[color-mix(in_oklab,var(--risk-critical)_16%,var(--card))] text-[var(--risk-critical)]">
          <WifiOff className="size-5" />
        </div>
        <h2 className="mt-4 text-lg font-semibold">{title}</h2>
        <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      </div>
    </div>
  );
}

export function EmptyState({
  title,
  message,
  icon: Icon = AlertTriangle,
}: {
  title: string;
  message: string;
  icon?: typeof AlertTriangle;
}) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-muted/10 p-6 text-center">
      <Icon className="mx-auto size-5 text-muted-foreground" />
      <h3 className="mt-3 text-sm font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{message}</p>
    </div>
  );
}
