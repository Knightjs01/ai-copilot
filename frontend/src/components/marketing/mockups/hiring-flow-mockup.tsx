import { Eye, EyeOff, Sparkles } from "lucide-react";

// The hero's overview visual -- distinct from every other mockup on the homepage (the Passport,
// Shadow board, AI assessment, ATS shell and Reveal mockups are each already shown in their own
// dedicated section further down the page). Rather than repeating one of those, or the Passport
// card a second time right above its own showcase section, this gives a first-glance summary of
// the whole story the page then walks through step by step: Callsign -> AI Match -> Reveal.
// Deliberately abstract and process-only -- no illustrative data, no numbers, nothing that could
// be mistaken for a real screenshot.

const STEPS = [
  {
    icon: EyeOff,
    title: "Engage anonymously",
    body: "No name, no CV upfront. Candidates apply under a Callsign.",
  },
  {
    icon: Sparkles,
    title: "Matched on evidence",
    body: "Phantom AI screens for skills and fit, not visibility.",
  },
  {
    icon: Eye,
    title: "Reveal, on their terms",
    body: "Identity is shared only when the candidate approves it.",
  },
];

export function HiringFlowMockup() {
  return (
    <div className="relative mx-auto w-full max-w-xs">
      <div
        className="absolute -inset-2 rounded-[28px] bg-gradient-to-br from-brand/20 via-electric/10 to-brand/20 blur-xl"
        aria-hidden
      />

      <div className="relative flex flex-col gap-6 rounded-3xl border border-border bg-card p-7 shadow-xl">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-brand">
            Phantom
          </p>
          <p className="text-lg font-bold tracking-tight text-foreground">How hiring works</p>
        </div>

        <div className="flex flex-col">
          {STEPS.map((step, i) => (
            <div key={step.title} className="relative flex gap-4">
              <div className="flex flex-col items-center">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                  <step.icon className="h-4 w-4" />
                </div>
                {i < STEPS.length - 1 && (
                  <span className="my-1 w-px flex-1 bg-border" aria-hidden />
                )}
              </div>
              <div className={`flex flex-col gap-1 ${i < STEPS.length - 1 ? "pb-6" : ""}`}>
                <p className="text-sm font-semibold text-foreground">{step.title}</p>
                <p className="text-xs leading-relaxed text-muted-foreground">{step.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
