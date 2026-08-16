"use client";

import * as React from "react";
import { Check, Lock, Minus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { COMPANY_PLANS, FEATURE_COMPARISON_ROWS, type FeatureRow } from "@/lib/pricing-config";

const CATEGORIES = Array.from(new Set(FEATURE_COMPARISON_ROWS.map((row) => row.category)));

function Cell({
  row,
  planId,
  onLockedClick,
}: {
  row: FeatureRow;
  planId: (typeof COMPANY_PLANS)[number]["id"];
  onLockedClick: (row: FeatureRow) => void;
}) {
  const value = row.values[planId];

  if (value === false) {
    if (row.proOnly) {
      return (
        <button
          type="button"
          onClick={() => onLockedClick(row)}
          className="inline-flex items-center justify-center text-muted-foreground/50 transition-colors hover:text-brand"
          aria-label={`${row.label} requires an upgrade`}
        >
          <Lock className="h-3.5 w-3.5" />
        </button>
      );
    }
    return <Minus className="h-3.5 w-3.5 text-muted-foreground/30" />;
  }

  if (value === true) {
    return <Check className="h-4 w-4 text-brand" />;
  }

  return <span className="text-xs text-foreground">{value}</span>;
}

export function PlanComparisonTableSection() {
  const [lockedRow, setLockedRow] = React.useState<FeatureRow | null>(null);

  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Compare every plan in detail
          </h2>
        </div>

        <div className="mt-10 overflow-x-auto rounded-2xl border border-border shadow-sm shadow-slate-900/[0.03]">
          <table className="w-full min-w-[640px] border-collapse bg-card text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/20">
                <th className="sticky left-0 z-10 bg-secondary/20 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Feature
                </th>
                {COMPANY_PLANS.map((plan) => (
                  <th
                    key={plan.id}
                    className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground"
                  >
                    {plan.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CATEGORIES.map((category) => (
                <React.Fragment key={category}>
                  <tr className="border-b border-border bg-secondary/30">
                    <td
                      colSpan={COMPANY_PLANS.length + 1}
                      className="sticky left-0 px-4 py-2 text-xs font-semibold text-foreground"
                    >
                      {category}
                    </td>
                  </tr>
                  {FEATURE_COMPARISON_ROWS.filter((row) => row.category === category).map(
                    (row) => (
                      <tr key={row.label} className="border-b border-border last:border-b-0">
                        <td className="sticky left-0 z-10 bg-card px-4 py-3 text-xs text-foreground">
                          {row.label}
                        </td>
                        {COMPANY_PLANS.map((plan) => (
                          <td key={plan.id} className="px-4 py-3 text-center">
                            <div className="flex items-center justify-center">
                              <Cell row={row} planId={plan.id} onLockedClick={setLockedRow} />
                            </div>
                          </td>
                        ))}
                      </tr>
                    )
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Dialog open={lockedRow !== null} onOpenChange={(open) => !open && setLockedRow(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{lockedRow?.label} is available on Scale Up</DialogTitle>
            <DialogDescription>
              Don&apos;t lose the talent you&apos;ve already discovered. Save privacy-conscious
              candidate intelligence and rediscover exceptional people when the next role opens.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => setLockedRow(null)}>
              Continue without {lockedRow?.label}
            </Button>
            <Button asChild variant="brand">
              <a href="/signup">Upgrade to Scale Up</a>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
