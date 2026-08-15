import { EyeOff, FileText } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { Button } from "@/components/ui/button";

export function JobApplicationMockup() {
  return (
    <BrowserFrame url="jobs.phantomhire.com/senior-backend-engineer" badge="Live now">
      <div className="flex flex-col gap-4">
        <div>
          <p className="text-sm font-semibold text-foreground">Senior Backend Engineer</p>
          <p className="text-xs text-muted-foreground">Confidential · Series C Fintech · Remote</p>
        </div>

        <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-3.5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand/10 text-xs font-semibold text-brand">
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
      </div>
    </BrowserFrame>
  );
}
