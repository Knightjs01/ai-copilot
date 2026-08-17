import { CheckCircle2, HelpCircle, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { CornerMarks } from "@/components/marketing/mockups/corner-marks";

// Mirrors the real shape of a PrescreenAssessment (fit rating + strengths/gaps/suggested
// questions/areas_to_probe, plus model_used/generated_at provenance) — this is the actual
// on-demand AI feature that exists today, not an invented live-interview co-pilot. Illustrative
// sample data, same convention as every other mockup here.
const STRENGTHS = [
  "Led a payments platform scaling to £50m+ volume",
  "6 years distributed systems",
  "Owns incident response for the core ledger service",
];
const GAPS = ["Hasn't described direct ownership vs. team contribution"];
const QUESTIONS = ["What specifically did you own within that platform?"];
const AREAS_TO_PROBE = ["Ownership scope", "Team size led", "On-call structure"];

export function AiAssessmentMockup() {
  return (
    <div className="relative">
      <CornerMarks />
      <BrowserFrame url="app.phantomhire.com/candidates/pulse-78" badge="Live now">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-mono text-sm font-semibold text-foreground">Pulse-78</p>
              <p className="text-xs text-muted-foreground">Pre-screen assessment</p>
            </div>
            <Badge variant="success">Strong Fit</Badge>
          </div>

          <div className="grid grid-cols-2 gap-2.5 rounded-xl border border-border bg-card p-3">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                model_used
              </p>
              <p className="mt-0.5 font-mono text-[11px] text-foreground">claude-sonnet-5</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                generated_at
              </p>
              <p className="mt-0.5 font-mono text-[11px] tabular-nums text-foreground">
                2026-08-17 · 3m ago
              </p>
            </div>
          </div>

          <div className="rounded-xl border border-success/20 bg-success/5 p-3.5">
            <p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-success">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Strong evidence
            </p>
            <ul className="mt-2 flex flex-col gap-1.5">
              {STRENGTHS.map((item) => (
                <li key={item} className="rounded-lg border border-success/10 bg-card/60 px-2.5 py-1.5 text-xs text-foreground/80">
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-warning/20 bg-warning/5 p-3.5">
            <p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-warning">
              <TriangleAlert className="h-3.5 w-3.5" />
              Missing evidence
            </p>
            <ul className="mt-2 flex flex-col gap-1.5">
              {GAPS.map((item) => (
                <li key={item} className="rounded-lg border border-warning/10 bg-card/60 px-2.5 py-1.5 text-xs text-foreground/80">
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-border bg-card p-3.5">
            <p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
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
            <div className="mt-2.5 flex flex-wrap gap-1.5 border-t border-border pt-2.5">
              {AREAS_TO_PROBE.map((area) => (
                <span
                  key={area}
                  className="rounded-full border border-border bg-secondary/40 px-2 py-0.5 font-mono text-[10px] text-foreground/80"
                >
                  {area}
                </span>
              ))}
            </div>
          </div>
        </div>
      </BrowserFrame>
    </div>
  );
}
