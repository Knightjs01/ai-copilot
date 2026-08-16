import Link from "next/link";

import { IntelligenceBreakdownMockup } from "@/components/marketing/mockups/intelligence-breakdown-mockup";
import { Button } from "@/components/ui/button";

export function IntelligenceHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Phantom Intelligence
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Your ATS tells you what happened. Phantom tells you what&apos;s next.
          </h1>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Real breakdowns of every pipeline, generated from your own project data — fit rating,
            status, source, and more. No market-wide claims, just what&apos;s actually happening
            in your search.
          </p>
          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring with Phantom</Link>
            </Button>
          </div>
        </div>

        <IntelligenceBreakdownMockup />
      </div>
    </section>
  );
}
