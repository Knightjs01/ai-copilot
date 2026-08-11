import Link from "next/link";

import { AtsMockup } from "@/components/marketing/mockups/ats-mockup";
import { Button } from "@/components/ui/button";

export function AtsShowcaseSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            The ATS · Live now
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            The pipeline your team already runs on
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Hiring projects, Callsigns instead of names, AI fit ratings, and a live dashboard of
            exactly what needs your attention next. This is the actual platform, not a concept.
          </p>
          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring with Phantom</Link>
            </Button>
          </div>
        </div>

        <AtsMockup />
      </div>
    </section>
  );
}
