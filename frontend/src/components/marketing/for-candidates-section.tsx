import { BadgeCheck, EyeOff, Flame, Wand2 } from "lucide-react";

const PROMISE = [
  {
    icon: EyeOff,
    title: "Anonymous by default",
    body: "You're a Callsign until you decide otherwise. No name, no photo, no employer history exposed to anyone browsing.",
  },
  {
    icon: Wand2,
    title: "AI-matched",
    body: "Matched to roles based on your actual skills and experience — not keywords, not guesswork.",
  },
  {
    icon: BadgeCheck,
    title: "Verified when it matters",
    body: "Identity and credentials confirmed only at the point a real opportunity is on the table — not before.",
  },
  {
    icon: Flame,
    title: "Zero-retention when it's done",
    body: "Once a search concludes, your data goes with Phantom. Nothing lingers in someone else's database.",
  },
];

export function ForCandidatesSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-20 lg:py-28">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            For candidates
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Explore your next move, quietly
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Your next role, without the risk of your current one finding out.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {PROMISE.map((item) => (
            <div key={item.title} className="flex flex-col gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary text-foreground">
                <item.icon className="h-5 w-5" />
              </div>
              <h3 className="text-sm font-semibold text-foreground">{item.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{item.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
