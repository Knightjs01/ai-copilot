import { JobApplicationMockup } from "@/components/marketing/mockups/job-application-mockup";
import { Badge } from "@/components/ui/badge";
import { SHADOW_APPLICATION_STATUS_LABEL } from "@/lib/status-display";
import type { ShadowApplicationStatus } from "@/lib/types";

const STATUS_FLOW: ShadowApplicationStatus[] = [
  "submitted",
  "under_review",
  "reveal_requested",
  "revealed",
];

export function ShadowHowItWorksSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">How applying works</p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            One click from your Passport. A real status you can track.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Apply with your existing Phantom Passport and get a fresh Callsign for this
            application. Your name, employer and contact details stay hidden until you choose to
            share them, and your original CV is never sent, only your reviewed and approved
            Passport.
          </p>

          <div className="flex flex-col gap-2">
            <p className="text-sm font-medium text-foreground">Track it end to end</p>
            <div className="flex flex-wrap items-center gap-2">
              {STATUS_FLOW.map((status, index) => (
                <span key={status} className="flex items-center gap-2">
                  <Badge variant="outline">{SHADOW_APPLICATION_STATUS_LABEL[status]}</Badge>
                  {index < STATUS_FLOW.length - 1 && (
                    <span className="text-muted-foreground">→</span>
                  )}
                </span>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              Or Declined / Withdrawn — every application has one real, current status, always
              visible to you.
            </p>
          </div>
        </div>

        <JobApplicationMockup />
      </div>
    </section>
  );
}
