import { Eye, ShieldCheck, Wallet } from "lucide-react";

const BELIEFS = [
  {
    icon: ShieldCheck,
    quote: "Privacy is the architecture, not a setting.",
    body: "Tenant isolation, encryption at rest, and mandatory step-up checks aren't optional toggles buried in a settings page. They're how every request is handled, for everyone, by default.",
  },
  {
    icon: Eye,
    quote: "Evidence over black boxes.",
    body: "A fit rating is only useful if you can see what it's based on. Every assessment comes with the strengths and gaps behind it, not just a score to trust blindly.",
  },
  {
    icon: Wallet,
    quote: "Free for the people it's about.",
    body: "Candidates never pay to build a Passport, explore Shadow, or be discovered. The people the platform exists to serve shouldn't have to buy their way in.",
  },
];

export function AboutBeliefsSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            What we believe
          </h2>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {BELIEFS.map((belief) => (
            <div
              key={belief.quote}
              className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-7 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand/10 text-brand">
                <belief.icon className="h-5 w-5" />
              </div>
              <p className="text-lg font-semibold leading-snug text-foreground">
                {belief.quote}
              </p>
              <p className="text-sm leading-relaxed text-muted-foreground">{belief.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
