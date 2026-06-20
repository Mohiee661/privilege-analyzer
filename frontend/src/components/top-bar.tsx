import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Bell, Command, Plus, Search, Sun } from "lucide-react";

export function TopBar() {
  const navigate = useNavigate();
  const [darkMode, setDarkMode] = useState(
    () => typeof document !== "undefined" && document.documentElement.classList.contains("dark"),
  );

  const toggleTheme = () => {
    const next = !document.documentElement.classList.contains("dark");
    document.documentElement.classList.toggle("dark", next);
    setDarkMode(next);
  };

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur">
      <div className="relative flex-1 max-w-2xl">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search identities, findings, emails, IDs..."
          className="h-9 w-full rounded-md border border-border bg-card pl-9 pr-16 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-1 focus:ring-ring"
        />
        <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
          <Command className="size-3" /> K
        </div>
      </div>

      <div className="ml-auto flex items-center gap-1.5">
        <button
          onClick={() => navigate({ to: "/risk-center" })}
          className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="size-4" /> Quick Action
        </button>
        <button
          onClick={() => navigate({ to: "/findings" })}
          className="relative inline-flex size-9 items-center justify-center rounded-md border border-border bg-card text-muted-foreground hover:text-foreground"
        >
          <Bell className="size-4" />
          <span className="absolute right-2 top-2 size-1.5 rounded-full bg-[var(--risk-critical)]" />
        </button>
        <button
          onClick={toggleTheme}
          className="inline-flex size-9 items-center justify-center rounded-md border border-border bg-card text-muted-foreground hover:text-foreground"
          aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
        >
          <Sun className="size-4" />
        </button>
        <div className="ml-1 flex items-center gap-2 rounded-md border border-border bg-card pl-1 pr-2.5 py-1">
          <div className="flex size-7 items-center justify-center rounded bg-secondary text-xs font-semibold text-secondary-foreground">
            AR
          </div>
          <div className="hidden sm:flex flex-col leading-tight">
            <span className="text-xs font-medium text-foreground">Alex Reyes</span>
            <span className="text-[10px] text-muted-foreground">CISO · Contoso</span>
          </div>
        </div>
      </div>
    </header>
  );
}
