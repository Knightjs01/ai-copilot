import { ScrollText, ShieldCheck } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { Button } from "@/components/ui/button";

export function RevealIdentityMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/projects/.../candidates/pulse-78" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 shrink-0 text-brand" />
          <p className="text-sm font-semibold text-foreground">Reveal Identity — Pulse-78</p>
        </div>

        <div className="rounded-xl border border-border bg-white p-3.5">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Reason
          </p>
          <p className="mt-1 text-xs text-foreground">
            Final interview scheduled — need a real name for the calendar invite.
          </p>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="brand" size="sm" tabIndex={-1}>
            Cancel
          </Button>
          <Button variant="secondary" size="sm" tabIndex={-1}>
            Reveal Identity
          </Button>
        </div>

        <div className="rounded-xl border border-border bg-white p-3.5">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Decrypted snapshot
          </p>
          <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
            <span className="text-muted-foreground">Name</span>
            <span className="text-right font-medium text-foreground">Jane Doe</span>
            <span className="text-muted-foreground">Email</span>
            <span className="text-right font-medium text-foreground">jane@example.com</span>
            <span className="text-muted-foreground">Original CV</span>
            <span className="text-right font-medium text-foreground">Not retained</span>
          </div>
        </div>

        <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <ScrollText className="h-3 w-3 shrink-0" />
          This reveal was logged — visible in the Historic Vault audit trail.
        </p>
      </div>
    </BrowserFrame>
  );
}
