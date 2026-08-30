import { Network, ShieldCheck, Sparkles } from "lucide-react";

const FEATURES = [
  {
    icon: Network,
    title: "Our network",
    body: "Recruitment experts who already know where to look, working your search alongside your own team rather than in place of it.",
  },
  {
    icon: Sparkles,
    title: "Our technology",
    body: "The same Phantom Passport, Shadow and AI matching your in-house recruiters use — no separate tools, no separate process.",
  },
  {
    icon: ShieldCheck,
    title: "Our insights",
    body: "Evidence-based recommendations, not gut feel — every introduction is grounded in real, verifiable candidate data.",
  },
];

export function TalentPartnersFeaturesSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="flex flex-col gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand/10 text-brand">
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
