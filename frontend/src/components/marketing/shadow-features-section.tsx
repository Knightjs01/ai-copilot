import { EyeOff, FileCheck2, PoundSterling, Search } from "lucide-react";

const FEATURES = [
  {
    icon: Search,
    title: "Search by skill",
    body: "Filter by seniority, remote preference and employment type, or search freely by title and summary. Built on the same real filters the live board runs on.",
  },
  {
    icon: PoundSterling,
    title: "Salary shown upfront",
    body: "Every listing that gives a range shows it on the card. No wasted conversations over a number that was never going to work.",
  },
  {
    icon: EyeOff,
    title: "Confidential listings",
    body: "Companies can list a role without naming themselves until they're ready, so a confidential search stays confidential on both sides.",
  },
  {
    icon: FileCheck2,
    title: "Apply once with your Passport",
    body: "No re-typing your CV for every role. Apply from your existing Phantom Passport, and get a fresh Callsign for each application.",
  },
];

export function ShadowFeaturesSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">What&apos;s in it</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Built for people who aren&apos;t applying anywhere else.
          </h2>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <feature.icon className="h-5 w-5" />
              </div>
              <h3 className="text-sm font-semibold text-foreground">{feature.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{feature.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
