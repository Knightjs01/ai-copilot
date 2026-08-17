import { Badge } from "@/components/ui/badge";
import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

// Mirrors the real two-stage PrescreenAssessment lifecycle: fit_rating/strengths/gaps/
// suggested_questions is generated before the call (useGeneratePrescreenAssessment), then
// handoff_recommendations is generated after the call (useGenerateHandoffRecommendations),
// gated on the recruiter's own prescreen_notes existing first. The middle step is explicitly
// human — Phantom AI never listens to or drafts the interview itself.
const STAGES = [
  {
    step: "01",
    kicker: "Before the call",
    title: "Generate assessment",
    tone: "brand" as const,
    body: "Fit rating, evidence, and questions to ask — from the role brief and the candidate's own record.",
    detail: "Strong Fit · 3 strengths evidenced · 1 gap to probe",
    meta: "candidates.pulse_78.prescreen_assessment",
  },
  {
    step: "02",
    kicker: "During the call",
    title: "You take the notes",
    tone: "neutral" as const,
    body: "The recruiter conducts the interview and writes up their own notes. Phantom AI has no part in this step.",
    detail: "prescreen_notes · authored by recruiter",
    meta: "no AI involvement — by design",
  },
  {
    step: "03",
    kicker: "After the call",
    title: "Generate recommendations",
    tone: "brand" as const,
    body: "Unlocks once your notes exist — Phantom AI drafts a handoff from the original evidence plus what you heard.",
    detail: "handoff_recommendations · ready to share",
    meta: "gated on prescreen_notes != null",
  },
];

export function AiLifecycleMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/candidates/pulse-78" badge="Live now">
      <div className="flex flex-col">
        {STAGES.map((stage, index) => (
          <div key={stage.step} className="flex gap-4">
            <div className="flex flex-col items-center">
              <span
                className={
                  stage.tone === "brand"
                    ? "flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand font-mono text-[11px] font-semibold text-brand-foreground"
                    : "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-border bg-card font-mono text-[11px] font-semibold text-muted-foreground"
                }
              >
                {stage.step}
              </span>
              {index < STAGES.length - 1 && <span className="my-1 w-px flex-1 bg-border" />}
            </div>

            <div className={index < STAGES.length - 1 ? "flex flex-1 flex-col gap-1.5 pb-5" : "flex flex-1 flex-col gap-1.5"}>
              <div className="flex items-center gap-2">
                <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  {stage.kicker}
                </p>
                {stage.tone === "neutral" && (
                  <Badge variant="neutral" className="text-[10px]">
                    Human
                  </Badge>
                )}
              </div>
              <p className="text-sm font-semibold text-foreground">{stage.title}</p>
              <p className="text-xs leading-relaxed text-foreground/80">{stage.body}</p>
              <div className="mt-1 rounded-lg border border-border bg-card px-3 py-2">
                <p className="text-[11px] text-muted-foreground">{stage.detail}</p>
                <p className="mt-1 font-mono text-[10px] text-muted-foreground/70">{stage.meta}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </BrowserFrame>
  );
}
