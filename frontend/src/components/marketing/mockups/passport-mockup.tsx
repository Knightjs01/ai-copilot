import { Lock, ShieldCheck, Vault } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

const SKILLS = ["Distributed Systems", "Go", "Platform Architecture"];

const PRIVATE_FIELDS = ["Name & photo", "Current employer"];

export function PassportMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/passport" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-3.5">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-brand/60 text-xs font-semibold text-brand">
            P-78
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-foreground">Pulse-78</p>
            <p className="truncate text-[11px] text-muted-foreground">
              Senior Backend Engineer · Remote
            </p>
          </div>
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border-2 border-brand/40">
            <span className="text-[11px] font-semibold text-brand">92%</span>
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card p-3.5">
          <div className="flex items-center gap-2.5">
            <Vault className="h-4 w-4 shrink-0 text-brand" />
            <p className="text-sm font-medium text-foreground">Candidate Vault</p>
          </div>
          <span className="shrink-0 rounded-full bg-brand/10 px-2.5 py-1 text-[11px] font-semibold text-brand">
            Approved · Version 3
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {SKILLS.map((skill) => (
            <span
              key={skill}
              className="rounded-full border border-border bg-card px-3 py-1 text-[11px] text-foreground/80"
            >
              {skill}
            </span>
          ))}
        </div>

        <div className="flex flex-col gap-1.5 rounded-xl border border-border bg-card p-3.5">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            <ShieldCheck className="h-3.5 w-3.5 text-brand" />
            What stays private
          </p>
          {PRIVATE_FIELDS.map((field) => (
            <p key={field} className="flex items-center gap-1.5 text-xs text-foreground/70">
              <Lock className="h-3 w-3 shrink-0 text-muted-foreground" />
              {field}
            </p>
          ))}
        </div>
      </div>
    </BrowserFrame>
  );
}
