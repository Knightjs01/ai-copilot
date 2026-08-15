import Link from "next/link";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

export function PricingFinalCtaSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-3xl px-6 py-16 text-center lg:py-20">
        <div className="flex flex-col items-center gap-5 rounded-3xl border border-border bg-card px-8 py-14 shadow-sm shadow-slate-900/[0.03]">
          <Sparkles className="h-8 w-8 text-brand" />
          <h2 className="max-w-xl text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            Ready to hire differently?
          </h2>
          <p className="max-w-lg text-muted-foreground">
            Build your first role for free. Discover people who aren&apos;t applying publicly.
            And keep control of the data you create along the way.
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
      </div>
    </section>
  );
}
