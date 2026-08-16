import Link from "next/link";

import { Button } from "@/components/ui/button";

export function IntelligenceFinalCtaSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-6 py-20 text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Real intelligence on your own pipeline, today.
        </h2>
        <p className="max-w-lg text-lg leading-relaxed text-muted-foreground">
          Every breakdown is generated from your own project data — nothing borrowed from the
          wider market.
        </p>
        <Button asChild variant="brand" size="lg">
          <Link href="/signup">Start hiring with Phantom</Link>
        </Button>
      </div>
    </section>
  );
}
