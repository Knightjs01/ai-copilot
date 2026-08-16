import { Briefcase, Layers, MapPin, Sparkles } from "lucide-react";

import { PassportDetailMockup } from "@/components/marketing/mockups/passport-detail-mockup";

// Grounded exactly in PhantomPassport's real fields (frontend/src/lib/types.ts:365-386) — nothing
// invented.
const FEATURES = [
  {
    icon: Sparkles,
    title: "Professional details",
    body: "Headline, seniority, years of experience, and a summary — the top-line facts a recruiter reads first.",
  },
  {
    icon: Layers,
    title: "Skills & industries",
    body: "The specific skills and industries you've actually worked in, not a keyword-matched guess.",
  },
  {
    icon: Briefcase,
    title: "Career history",
    body: "Every role you've held, with responsibilities and achievements — each entry carries a real employer name only you can see, and a separate anonymized label everyone else does.",
  },
  {
    icon: MapPin,
    title: "Logistics",
    body: "Location, remote preference, salary range, notice period, and what you're looking for next — set once, honored everywhere.",
  },
];

export function PassportFeaturesSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            What&apos;s in it
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            One record, built once.
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-10 lg:grid-cols-2 lg:items-center">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                  <feature.icon className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-semibold text-foreground">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{feature.body}</p>
              </div>
            ))}
          </div>

          <PassportDetailMockup />
        </div>
      </div>
    </section>
  );
}
