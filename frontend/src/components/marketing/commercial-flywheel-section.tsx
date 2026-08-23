import { ArrowRight } from "lucide-react";

const FLYWHEEL_STEPS = [
  "Candidate",
  "Free Phantom Passport",
  "Shadow",
  "Anonymous opportunities",
  "Companies",
  "Phantom ATS & AI screening",
  "Successful hiring",
  "Talent Memory (Preview)",
  "Future rediscovery",
  "More valuable platform",
];

export function CommercialFlywheelSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto max-w-5xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Why Phantom can give candidates the platform for free
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            The more candidates create a Passport, the more valuable Shadow becomes. The more
            companies join, the more valuable Phantom becomes to candidates.
          </p>
        </div>

        <div className="mt-12 flex flex-wrap items-center justify-center gap-x-2 gap-y-4">
          {FLYWHEEL_STEPS.map((step, i) => (
            <div key={step} className="flex items-center gap-2">
              <span className="rounded-full border border-border bg-card px-3.5 py-1.5 text-xs font-medium text-foreground shadow-sm shadow-slate-900/[0.03]">
                {step}
              </span>
              {i < FLYWHEEL_STEPS.length - 1 && (
                <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/40" aria-hidden />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
