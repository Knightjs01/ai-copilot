import { AtsAnalyticsMockup } from "@/components/marketing/mockups/ats-analytics-mockup";

export function AtsAnalyticsSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Analytics & action items
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Not just what happened. What to do next.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Every project breaks down fit rating, pipeline stage, source, and salary expectations
            in real time. And instead of a static report, your dashboard surfaces exactly what
            needs a decision from you today: who&apos;s ready to advance, who needs an interview
            booked, who&apos;s waiting on a prescreen, and which project still needs hiring
            manager priorities.
          </p>
        </div>

        <AtsAnalyticsMockup />
      </div>
    </section>
  );
}
