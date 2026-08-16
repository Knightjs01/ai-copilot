import { CalendarClock, EyeOff, RefreshCw, ShieldCheck } from "lucide-react";

const TRUST_POINTS = [
  {
    icon: ShieldCheck,
    title: "Always shows its evidence",
    body: "Every fit rating comes with the strengths, gaps, and highlights it's based on — never just a verdict.",
  },
  {
    icon: EyeOff,
    title: "Never listens live",
    body: "Phantom AI has no access to your calls. It works from written records, before and after, not during.",
  },
  {
    icon: CalendarClock,
    title: "Dated and attributed",
    body: "Every output shows when it was generated and which model produced it.",
  },
  {
    icon: RefreshCw,
    title: "You generate it, you regenerate it",
    body: "Nothing runs automatically or silently. You trigger every assessment and every handoff.",
  },
];

export function AiTrustSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16 lg:py-20">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand">No black box</p>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {TRUST_POINTS.map((point) => (
            <div key={point.title} className="flex flex-col gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <point.icon className="h-4 w-4" />
              </div>
              <p className="text-sm font-semibold text-foreground">{point.title}</p>
              <p className="text-sm leading-relaxed text-muted-foreground">{point.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
