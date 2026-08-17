import { EyeOff, Flame, Vault } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { CornerMarks } from "@/components/marketing/mockups/corner-marks";

const MATCHES = [
  { title: "Senior Backend Engineer", match: 92 },
  { title: "Staff Platform Engineer", match: 87 },
  { title: "Principal Engineer, Payments", match: 81 },
];

export function CandidatePortalMockup() {
  return (
    <div className="relative">
      <CornerMarks />
      <BrowserFrame url="app.phantomhire.com/passport" badge="Live now">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-3.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand/10 font-mono text-xs font-semibold text-brand">
              P-78
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground">Pulse-78</p>
              <p className="flex items-center gap-1 text-[11px] text-muted-foreground">
                <EyeOff className="h-3 w-3 shrink-0" />
                Identity hidden, reveal only when you choose
              </p>
            </div>
            <div className="shrink-0 text-right">
              <p className="font-mono text-sm font-semibold tabular-nums text-foreground">92%</p>
              <p className="text-[10px] text-muted-foreground">complete</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <div className="flex items-center gap-2.5 rounded-xl border border-border bg-card p-3">
              <Vault className="h-4 w-4 shrink-0 text-brand" />
              <div>
                <p className="text-xs font-medium text-foreground">Candidate Vault</p>
                <p className="font-mono text-[10px] text-success">Approved · v3</p>
              </div>
            </div>
            <div className="flex items-center gap-2.5 rounded-xl border border-border bg-card p-3">
              <Flame className="h-4 w-4 shrink-0 text-brand" />
              <div>
                <p className="text-xs font-medium text-foreground">Zero-Retention</p>
                <p className="text-[10px] text-muted-foreground">Purged on close</p>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Matched to you
            </p>
            {MATCHES.map((role) => (
              <div
                key={role.title}
                className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card p-3"
              >
                <p className="text-sm font-medium text-foreground">{role.title}</p>
                <span className="shrink-0 rounded-full bg-success/10 px-2.5 py-1 font-mono text-[11px] font-semibold tabular-nums text-success">
                  {role.match}% match
                </span>
              </div>
            ))}
          </div>
        </div>
      </BrowserFrame>
    </div>
  );
}
