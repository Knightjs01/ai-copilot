import { ChevronDown, DatabaseZap, ShieldCheck, UserCheck } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

// Grounded exactly in SECURITY.md §2: three independent, deliberately redundant layers
// protecting candidates/projects. Not a UI screenshot like every other mockup on this site —
// an architecture diagram, since that's what's actually true here.
const LAYERS = [
  {
    icon: DatabaseZap,
    title: "No DB grant",
    body: "The pre-auth database role has zero SELECT/INSERT privileges on candidate or project tables — not policy, a missing grant.",
  },
  {
    icon: ShieldCheck,
    title: "Row-Level Security",
    body: "Every tenant-owned table is scoped to your company at the database level, enforced even against a compromised query.",
  },
  {
    icon: UserCheck,
    title: "App-layer re-check",
    body: "The application independently re-verifies company ownership on every read, regardless of what the database already enforced.",
  },
];

export function TenantIsolationMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/security/architecture" badge="Live now">
      <div className="flex flex-col">
        {LAYERS.map((layer, index) => (
          <div key={layer.title} className="flex flex-col items-center">
            <div className="flex w-full items-start gap-3 rounded-xl border border-border bg-card p-4">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <layer.icon className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">{layer.title}</p>
                <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
                  {layer.body}
                </p>
              </div>
            </div>
            {index < LAYERS.length - 1 && (
              <ChevronDown className="my-1.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
            )}
          </div>
        ))}
      </div>
    </BrowserFrame>
  );
}
