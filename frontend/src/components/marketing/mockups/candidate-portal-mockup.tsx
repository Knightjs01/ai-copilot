import { EyeOff, Flame, Vault } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { CornerMarks } from "@/components/marketing/mockups/corner-marks";
import { Badge } from "@/components/ui/badge";
import { FIT_RATING_VARIANT } from "@/lib/status-display";
import type { FitRating } from "@/lib/types";

// No numeric "AI match %" -- the real product only ever computes the 4-tier FitRating
// (Strong/Good/Possible/Weak Fit), never a percentage. See ats-app-shell-mockup.tsx's own
// comment for the same rule, applied consistently here.
const MATCHES: { title: string; fit: FitRating }[] = [
  { title: "Senior Backend Engineer", fit: "Strong Fit" },
  { title: "Staff Platform Engineer", fit: "Strong Fit" },
  { title: "Principal Engineer, Payments", fit: "Good Fit" },
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
                <Badge variant={FIT_RATING_VARIANT[role.fit]} className="shrink-0">
                  {role.fit}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </BrowserFrame>
    </div>
  );
}
