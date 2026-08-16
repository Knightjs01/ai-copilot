import { TrendingUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";

// None of these have any backend basis today — confirmed against ProjectAnalytics,
// DashboardStats, and HistoricVaultOverview, which only ever compute within-project figures.
// Framed explicitly as roadmap, not live output.
const ROADMAP_ITEMS = [
  "Talent market supply — how many people plausibly fit a role, before you post it",
  "Skill scarcity signals across the roles you're hiring for",
  "Salary intelligence benchmarked against comparable searches",
  "Historical talent rediscovery across your own past projects",
];

export function IntelligenceRoadmapSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              What we&apos;re building next
            </p>
            <Badge variant="outline">Preview</Badge>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Beyond your own pipeline.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Project analytics look at your own data. The next layer of Phantom Intelligence looks
            wider — illustrative of the direction, not available today.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {ROADMAP_ITEMS.map((item) => (
            <div
              key={item}
              className="flex items-start gap-2.5 rounded-xl border border-dashed border-border bg-secondary/20 p-4"
            >
              <TrendingUp className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <p className="text-sm leading-relaxed text-muted-foreground">{item}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
