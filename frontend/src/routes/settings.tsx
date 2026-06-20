import type { ReactNode } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Bell, Cloud, Key, Palette, User } from "lucide-react";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings · IRIP" }] }),
  component: Settings,
});

const platforms = [
  { name: "Active Directory", status: "Connected", lastSync: "2 min ago" },
  { name: "Azure AD / Entra ID", status: "Connected", lastSync: "3 min ago" },
  { name: "AWS IAM", status: "Connected", lastSync: "5 min ago" },
  { name: "Okta", status: "Connected", lastSync: "1 min ago" },
  { name: "Salesforce", status: "Degraded", lastSync: "27 min ago" },
];

function Settings() {
  return (
    <div className="p-6 space-y-6 max-w-[1100px] mx-auto">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Configure your IRIP workspace, integrations, and preferences.
        </p>
      </div>

      <Section
        icon={<User className="size-4" />}
        title="User Preferences"
        desc="How IRIP appears for your account."
      >
        <Row label="Display name" value="Alex Reyes" />
        <Row label="Email" value="alex.reyes@contoso.com" />
        <Row label="Role" value="CISO" />
      </Section>

      <Section
        icon={<Palette className="size-4" />}
        title="Theme"
        desc="Visual appearance of the workspace."
      >
        <div className="flex gap-2">
          <button className="rounded-md border border-primary bg-primary/10 px-3 py-2 text-sm font-medium text-primary">
            Dark · Default
          </button>
          <button className="rounded-md border border-border bg-card px-3 py-2 text-sm text-muted-foreground">
            High contrast
          </button>
        </div>
      </Section>

      <Section
        icon={<Bell className="size-4" />}
        title="Notifications"
        desc="When IRIP alerts you."
      >
        <Toggle
          label="Critical risk alerts"
          desc="Email + in-app immediately on critical detection."
          defaultChecked
        />
        <Toggle
          label="Daily summary digest"
          desc="One email per day with new findings overview."
          defaultChecked
        />
        <Toggle
          label="Offboarding gap detection"
          desc="Alert when an offboarded identity retains access."
          defaultChecked
        />
        <Toggle label="Weekly executive report" desc="Sent every Monday 09:00 to your inbox." />
      </Section>

      <Section
        icon={<Key className="size-4" />}
        title="API Configuration"
        desc="Programmatic access to IRIP APIs."
      >
        <div className="rounded-md border border-border bg-muted/30 p-3 font-mono text-xs">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">API Endpoint</span>
            <code className="text-primary">https://api.irip.contoso.com/v1</code>
          </div>
          <div className="mt-2 flex items-center justify-between">
            <span className="text-muted-foreground">Token (last rotated 14 days ago)</span>
            <code>irip_sk_••••••••••••a3f9</code>
          </div>
        </div>
        <button className="mt-3 rounded-md border border-border bg-card px-3 py-2 text-sm hover:border-primary/30">
          Rotate token
        </button>
      </Section>

      <Section
        icon={<Cloud className="size-4" />}
        title="Platform Integrations"
        desc="Connected identity sources feeding into IRIP."
      >
        <div className="rounded-md border border-border overflow-hidden">
          {platforms.map((p, idx) => (
            <div
              key={p.name}
              className={`flex items-center justify-between px-4 py-3 ${idx > 0 ? "border-t border-border" : ""}`}
            >
              <div>
                <div className="text-sm font-medium">{p.name}</div>
                <div className="text-xs text-muted-foreground mt-0.5">Last sync · {p.lastSync}</div>
              </div>
              <span
                className={`inline-flex items-center gap-1.5 text-xs ${p.status === "Connected" ? "text-[var(--risk-low)]" : "text-[var(--risk-high)]"}`}
              >
                <span className="size-1.5 rounded-full bg-current" /> {p.status}
              </span>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

function Section({
  icon,
  title,
  desc,
  children,
}: {
  icon: ReactNode;
  title: string;
  desc: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-lg border border-border bg-card">
      <header className="flex items-center gap-3 border-b border-border px-5 py-4">
        <div className="flex size-8 items-center justify-center rounded-md bg-muted text-primary">
          {icon}
        </div>
        <div>
          <h3 className="text-sm font-semibold">{title}</h3>
          <p className="text-xs text-muted-foreground">{desc}</p>
        </div>
      </header>
      <div className="p-5 space-y-3">{children}</div>
    </section>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border last:border-0 pb-2 last:pb-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

function Toggle({
  label,
  desc,
  defaultChecked,
}: {
  label: string;
  desc: string;
  defaultChecked?: boolean;
}) {
  return (
    <label className="flex items-center justify-between gap-3 cursor-pointer">
      <div>
        <div className="text-sm font-medium">{label}</div>
        <div className="text-xs text-muted-foreground">{desc}</div>
      </div>
      <input
        type="checkbox"
        defaultChecked={defaultChecked}
        className="size-4 accent-[var(--primary)]"
      />
    </label>
  );
}
