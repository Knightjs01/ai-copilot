import { EyeOff, Lock, Sparkles, UserRound } from "lucide-react";

const POINTS = [
  {
    icon: UserRound,
    title: "Passport",
    body: "One reusable, verifiable candidate identity, built once, used everywhere on Phantom.",
  },
  {
    icon: EyeOff,
    title: "Shadow",
    body: "An anonymous job board where candidates discover roles under a Callsign, not a name.",
  },
  {
    icon: Sparkles,
    title: "Intelligence",
    body: "AI that matches on skills and evidence, and, over time, learns your organisation's hiring patterns.",
  },
  {
    icon: Lock,
    title: "Privacy",
    body: "Data minimisation by default, with project-specific information that can be permanently destroyed.",
  },
];

export function WhyPhantomDifferentSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Why Phantom is different
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            Traditional ATS platforms help you manage candidates you already know. Traditional
            job boards reach people actively looking. Phantom discovers high-quality talent who
            may never publicly advertise that they&apos;re looking.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {POINTS.map((point) => (
            <div key={point.title} className="flex flex-col gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <point.icon className="h-5 w-5" />
              </div>
              <h3 className="text-sm font-semibold text-foreground">{point.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{point.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
