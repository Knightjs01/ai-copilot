import { MessageSquareText } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SHADOW_APPLICATION_STATUS_LABEL } from "@/lib/status-display";

// The real, two-sided Shadow Reveal Request flow — genuinely distinct from Identity Vault's
// Owner-initiated reveal (shown via RevealIdentityMockup on /trust and /ats). Here the COMPANY
// requests disclosure with a reason, and the CANDIDATE approves or declines it — nothing is
// automatic. Real ShadowApplicationStatus lifecycle, real SHADOW_APPLICATION_STATUS_LABEL map.
export function ShadowRevealRequestMockup() {
  return (
    <BrowserFrame url="shadow.phantomhire.com/applications/echo-14" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-foreground">Senior Backend Engineer</p>
            <p className="text-xs text-muted-foreground">Applied as Echo-14</p>
          </div>
          <Badge variant="warning">{SHADOW_APPLICATION_STATUS_LABEL.reveal_requested}</Badge>
        </div>

        <div className="rounded-xl border border-border bg-card p-3.5">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            <MessageSquareText className="h-3 w-3 shrink-0" />
            Company&apos;s reason
          </p>
          <p className="mt-1.5 text-xs text-foreground">
            We&apos;d like to schedule your final interview and need your name and contact details
            for the calendar invite.
          </p>
        </div>

        <p className="text-xs text-muted-foreground">
          Only you can approve this. Nothing is shared automatically.
        </p>

        <div className="flex justify-end gap-2">
          <Button variant="secondary" size="sm" tabIndex={-1}>
            Decline
          </Button>
          <Button variant="brand" size="sm" tabIndex={-1}>
            Approve reveal
          </Button>
        </div>
      </div>
    </BrowserFrame>
  );
}
