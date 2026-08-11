import { JobBoardMockup } from "@/components/marketing/mockups/job-board-mockup";

export function JobBoardShowcaseSection() {
  return (
    <section className="border-t border-border bg-slate-50">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="order-2 lg:order-1">
          <JobBoardMockup />
        </div>

        <div className="order-1 flex flex-col gap-5 lg:order-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            The Job Board · Live now
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Roles worth discovering, employers worth trusting
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Candidates browse and apply without a profile that outs them to their current
            employer. Companies can list a role without naming themselves until they&apos;re
            ready to.
          </p>
        </div>
      </div>
    </section>
  );
}
