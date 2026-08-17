import { Check, EyeOff, FileText } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { Button } from "@/components/ui/button";
import { SHADOW_APPLICATION_STATUS_LABEL } from "@/lib/status-display";
import type { ShadowApplicationStatus } from "@/lib/types";

// Real ShadowApplicationStatus lifecycle (submitted → under_review → reveal_requested →
// revealed/declined/withdrawn) shown as a compact tracker beneath the real apply mechanic.
const TRACKER: ShadowApplicationStatus[] = ["submitted", "under_review", "reveal_requested", "revealed"];

export function JobApplicationMockup() {
  return (
    <BrowserFrame url="jobs.phantomhire.com/senior-backend-engineer" badge="Live now">
      <div className="flex flex-col gap-4">
        <div>
          <p className="text-sm font-semibold text-foreground">Senior Backend Engineer</p>
          <p className="text-xs text-muted-foreground">Confidential · Series C Fintech · Remote</p>
        </div>

        <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-3.5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand/10 font-mono text-xs font-semibold text-brand">
            E-14
          </div>
          <div>
            <p className="text-xs font-medium text-foreground">You&apos;ll apply as Echo-14</p>
            <p className="flex items-center gap-1 text-[11px] text-muted-foreground">
              <EyeOff className="h-3 w-3 shrink-0" />
              Name, employer and contact details stay hidden until you choose to share them
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-xl border border-dashed border-border bg-card p-3.5">
          <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
          <p className="text-xs text-muted-foreground">resume.pdf, auto-redacted before it&apos;s shared</p>
        </div>

        <Button variant="brand" size="sm" className="w-full" tabIndex={-1}>
          Apply as Echo-14
        </Button>

        <div className="rounded-xl border border-border bg-card p-3.5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Track your application
          </p>
          <div className="mt-2.5 flex items-center gap-1.5">
            {TRACKER.map((status, index) => (
              <div key={status} className="flex flex-1 items-center gap-1.5">
                <div className="flex flex-col items-center gap-1">
                  <span
                    className={
                      index === 0
                        ? "flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand"
                        : "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-border bg-background"
                    }
                  >
                    {index === 0 && <Check className="h-3 w-3 text-brand-foreground" />}
                  </span>
                  <span className="whitespace-nowrap font-mono text-[9px] text-muted-foreground">
                    {SHADOW_APPLICATION_STATUS_LABEL[status]}
                  </span>
                </div>
                {index < TRACKER.length - 1 && <span className="h-px flex-1 bg-border" />}
              </div>
            ))}
          </div>
        </div>
      </div>
    </BrowserFrame>
  );
}
