import { BarChart3, Target } from "lucide-react";

const BREAKDOWN_FIELDS = [
  "status_breakdown",
  "fit_rating_breakdown",
  "prescreen_outcome_breakdown",
  "source_breakdown",
  "agency_breakdown",
  "salary_stats",
  "notice_period_breakdown",
];

export function IntelligenceCapabilitiesSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            What&apos;s real today
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Two real sources of intelligence, nothing invented.
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
              <BarChart3 className="h-5 w-5" />
            </div>
            <p className="text-sm font-semibold text-foreground">Project analytics</p>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Every project computes real breakdowns of its own pipeline — where candidates are,
              how they were sourced, what they&apos;re asking for.
            </p>
            <div className="flex flex-wrap gap-1.5">
              {BREAKDOWN_FIELDS.map((field) => (
                <span
                  key={field}
                  className="rounded-full border border-border bg-secondary/40 px-2.5 py-1 font-mono text-[10px] text-muted-foreground"
                >
                  {field}
                </span>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
              <Target className="h-5 w-5" />
            </div>
            <p className="text-sm font-semibold text-foreground">Hiring manager alignment</p>
            <p className="text-sm leading-relaxed text-muted-foreground">
              A hiring manager submits their top priorities once. Phantom AI compares every
              candidate&apos;s own record against that list, so recruiters see exactly what&apos;s
              evidenced and what still needs probing — without a status meeting.
            </p>
            <div className="flex flex-wrap gap-1.5">
              {["top_requirements", "highlights"].map((field) => (
                <span
                  key={field}
                  className="rounded-full border border-border bg-secondary/40 px-2.5 py-1 font-mono text-[10px] text-muted-foreground"
                >
                  {field}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
