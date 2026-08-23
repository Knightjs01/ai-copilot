import Link from "next/link";

import { Button } from "@/components/ui/button";

export function PricingFinalCtaSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-6 py-20 text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Build a better way to hire.
        </h2>
        <p className="max-w-lg text-lg leading-relaxed text-muted-foreground">
          Discover people who aren&apos;t applying publicly, and keep control of the data you
          create along the way.
        </p>
        <Button asChild variant="brand" size="lg">
          <Link href="/signup">Get Started</Link>
        </Button>
        <p className="text-xs text-muted-foreground">No credit card required.</p>
      </div>
    </section>
  );
}
