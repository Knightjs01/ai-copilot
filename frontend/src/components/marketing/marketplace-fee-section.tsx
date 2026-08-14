import Link from "next/link";

import { Button } from "@/components/ui/button";
import { MARKETPLACE_FEE } from "@/lib/pricing-config";

export function MarketplaceFeeSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-3xl px-6 py-16 text-center lg:py-20">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Only want to pay when you hire?
        </h2>
        <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
          Use Phantom as a talent marketplace without committing to a subscription. Perfect for
          companies that want access to Phantom&apos;s anonymous talent network without adopting
          the full ATS.
        </p>

        <div className="mx-auto mt-10 flex max-w-md flex-col items-center gap-4 rounded-2xl border border-border bg-white p-8 shadow-sm shadow-slate-900/[0.03]">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Phantom Marketplace
          </p>
          <div className="flex items-end gap-2">
            <span className="text-4xl font-semibold tracking-tight text-foreground">
              £{MARKETPLACE_FEE.upfrontCost}
            </span>
            <span className="pb-1 text-sm text-muted-foreground">upfront</span>
          </div>
          <p className="text-sm text-muted-foreground">
            {MARKETPLACE_FEE.description} Indicative:{" "}
            {MARKETPLACE_FEE.percentOfFirstYearSalary}% of first-year base salary.
          </p>
          <Button asChild variant="brand" size="lg">
            <Link href="/signup">Explore Marketplace Hiring</Link>
          </Button>
        </div>

        <p className="mt-6 text-xs text-muted-foreground">
          This is an alternative commercial model, not an additional charge stacked on top of a
          SaaS subscription unless explicitly configured.
        </p>
      </div>
    </section>
  );
}
