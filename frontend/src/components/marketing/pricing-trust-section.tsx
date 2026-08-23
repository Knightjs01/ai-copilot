import { Brain, EyeOff, Flame, Lock, Puzzle, ShieldCheck } from "lucide-react";

const TRUST_POINTS = [
  {
    icon: Lock,
    title: "Protected Identity",
    body: "Candidate identity is separated from their professional profile.",
  },
  {
    icon: EyeOff,
    title: "Anonymous Callsigns",
    body: "Candidates can engage without immediately revealing their identity.",
  },
  {
    icon: Brain,
    title: "Controlled AI Context",
    body: "AI access follows project and permission boundaries.",
  },
  {
    icon: Flame,
    title: "Project Purge",
    body: "Project-specific data can be destroyed according to configured policy.",
  },
  {
    icon: Puzzle,
    title: "Talent Memory (Preview)",
    body: "The direction we're building toward: retain only the appropriate intelligence needed for future matching. Not available today.",
  },
  {
    icon: ShieldCheck,
    title: "Enterprise Controls",
    body: "Permissions, retention, audit and security controls for organisations.",
  },
];

export function PricingTrustSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Built around data minimisation
          </h2>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {TRUST_POINTS.map((point) => (
            <div
              key={point.title}
              className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]"
            >
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
