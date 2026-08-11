import { BadgeCheck, EyeOff, Flame, Wand2 } from "lucide-react";

const PROMISE = [
  {
    icon: EyeOff,
    title: "Anonymous by default",
    body: "You're a Callsign the moment you join — not a name, not a photo, not an employer history sitting in front of anyone browsing. Nobody sees who you are unless you decide to show them.",
  },
  {
    icon: Wand2,
    title: "AI-matched",
    body: "Phantom reads your actual skills and experience and matches you to roles worth your time — not a keyword-matching engine guessing from a resume.",
  },
  {
    icon: BadgeCheck,
    title: "Verified when it matters",
    body: "Identity and credentials only get confirmed once there's a real opportunity on the table — not before, and never as a condition of just browsing.",
  },
  {
    icon: Flame,
    title: "Zero-retention when it's done",
    body: "Once your search concludes, your data goes with Phantom — the same disappearing act companies get, applied to you. Nothing lingers in a database you never agreed to be in.",
  },
];

export function JobSeekersPromiseSection() {
  return (
    <section className="border-t border-border bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-20 lg:py-28">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            The same anonymity companies get — built for you too
          </h2>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-8 sm:grid-cols-2">
          {PROMISE.map((item) => (
            <div key={item.title} className="flex flex-col gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <item.icon className="h-5 w-5" />
              </div>
              <h3 className="text-base font-semibold text-foreground">{item.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{item.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
