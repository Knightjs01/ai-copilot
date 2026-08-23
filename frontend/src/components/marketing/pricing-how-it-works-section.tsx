import { Briefcase, Search, Sparkles } from "lucide-react";

const STEPS = [
  {
    icon: Briefcase,
    step: "1",
    title: "Build",
    body: "Run your hiring process on Phantom ATS: roles, pipeline, interviews, and your team, in one place.",
  },
  {
    icon: Search,
    step: "2",
    title: "Discover",
    body: "Post to Shadow to reach candidates who aren't applying anywhere publicly, engaging anonymously until they choose to step forward.",
  },
  {
    icon: Sparkles,
    step: "3",
    title: "Match",
    body: "Phantom AI screens and ranks candidates on skills and evidence, so your team's time goes to the right conversations first.",
  },
];

export function PricingHowItWorksSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            One platform, three ways to hire
          </h2>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 lg:grid-cols-3">
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
      </div>
    </section>
  );
}
