import Link from "next/link";

import { Button } from "@/components/ui/button";

export function PricingFinalCtaSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-6 py-20 text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Ready to hire differently?
        </h2>
        <p className="max-w-lg text-lg leading-relaxed text-muted-foreground">
          Build your first role for free. Discover people who aren&apos;t applying publicly. And
          keep control of the data you create along the way.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button asChild variant="brand" size="lg">
            <Link href="/signup">Start Hiring Free</Link>
          </Button>
          <Button asChild variant="secondary" size="lg">
            <Link href="/shadow/signup">Create Your Phantom Passport</Link>
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">No credit card required.</p>
      </div>
    </section>
  );
}
