import { CheckCircle2, FileUp, PenLine, ShieldCheck } from "lucide-react";

const STEPS = [
  {
    icon: FileUp,
    step: "1",
    title: "Upload your CV",
    body: "We extract and structure it into a draft Passport — no blank form to fill in from scratch.",
  },
  {
    icon: PenLine,
    step: "2",
    title: "Review and edit",
    body: "Everything the parser produced is yours to correct, rewrite, or add to before anything is saved as final.",
  },
  {
    icon: ShieldCheck,
    step: "3",
    title: "Approve a version",
    body: "Approving creates a fixed snapshot — the exact version that gets sent when you apply.",
  },
];

export function PassportHowItWorksSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            How it&apos;s built
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Nothing is discoverable until you approve it.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            No recruiter sees a draft, a half-finished profile, or a work-in-progress. Until you
            approve a version, your Passport doesn&apos;t exist to anyone but you.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {STEPS.map((step) => (
            <div
              key={step.title}
              className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-7 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand text-sm font-semibold text-brand-foreground">
                  {step.step}
                </div>
                <step.icon className="h-4 w-4 text-brand" />
              </div>
              <h3 className="text-base font-semibold text-foreground">{step.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{step.body}</p>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2.5 rounded-xl border border-brand/20 bg-brand/5 px-4 py-3">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-brand" />
          <p className="text-sm text-foreground">
            Every approval creates a new immutable version — you can always see exactly what was
            sent, and when.
          </p>
        </div>
      </div>
    </section>
  );
}
