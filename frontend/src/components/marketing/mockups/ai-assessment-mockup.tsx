import { CheckCircle2, HelpCircle, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

// Mirrors the real shape of a PrescreenAssessment (fit rating + strengths/gaps/suggested
// questions) — this is the actual on-demand AI feature that exists today, not an invented
// live-interview co-pilot. Illustrative sample data, same convention as every other mockup here.
const STRENGTHS = ["Led a payments platform scaling to £50m+ volume", "6 years distributed systems"];
const GAPS = ["Hasn't described direct ownership vs. team contribution"];
const QUESTIONS = ["What specifically did you own within that platform?"];

export function AiAssessmentMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/candidates/pulse-78" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-foreground">Pulse-78</p>
            <p className="text-xs text-muted-foreground">Pre-screen assessment</p>
          </div>
          <Badge variant="success">Strong Fit</Badge>
        </div>

        <div className="rounded-xl border border-success/20 bg-success/5 p-3.5">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-success">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Strong evidence
          </p>
          <ul className="mt-2 flex flex-col gap-1.5">
            {STRENGTHS.map((item) => (
              <li key={item} className="text-xs text-foreground/80">
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border border-warning/20 bg-warning/5 p-3.5">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-warning">
            <TriangleAlert className="h-3.5 w-3.5" />
            Missing evidence
          </p>
          <ul className="mt-2 flex flex-col gap-1.5">
            {GAPS.map((item) => (
              <li key={item} className="text-xs text-foreground/80">
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border border-border bg-card p-3.5">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            <HelpCircle className="h-3.5 w-3.5" />
            Ask this next
          </p>
          <ul className="mt-2 flex flex-col gap-1.5">
            {QUESTIONS.map((item) => (
              <li key={item} className="text-xs text-foreground/80">
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </BrowserFrame>
  );
}
