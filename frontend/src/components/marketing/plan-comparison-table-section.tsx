import * as React from "react";
import { Check, Minus } from "lucide-react";

import { getFeatureComparisonRows, type CompanyPlan, type FeatureRow } from "@/lib/pricing-config";

function Cell({ row, planId }: { row: FeatureRow; planId: CompanyPlan["id"] }) {
  const value = row.values[planId];

  if (value === false) {
    return <Minus className="h-3.5 w-3.5 text-muted-foreground/30" />;
  }

  if (value === true) {
    return <Check className="h-4 w-4 text-brand" />;
  }

  return <span className="text-xs text-foreground">{value}</span>;
}

export function PlanComparisonTableSection({ plans }: { plans: CompanyPlan[] }) {
  const rows = getFeatureComparisonRows(plans);
  const categories = Array.from(new Set(rows.map((row) => row.category)));

  return (
    <section id="compare-plans" className="border-t border-border scroll-mt-20">
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
                {plans.map((plan) => (
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
              {categories.map((category) => (
                <React.Fragment key={category}>
                  <tr className="border-b border-border bg-secondary/30">
                    <td
                      colSpan={plans.length + 1}
                      className="sticky left-0 px-4 py-2 text-xs font-semibold text-foreground"
                    >
                      {category}
                    </td>
                  </tr>
                  {rows
                    .filter((row) => row.category === category)
                    .map((row) => (
                      <tr key={row.label} className="border-b border-border last:border-b-0">
                        <td className="sticky left-0 z-10 bg-card px-4 py-3 text-xs text-foreground">
                          {row.label}
                        </td>
                        {plans.map((plan) => (
                          <td key={plan.id} className="px-4 py-3 text-center">
                            <div className="flex items-center justify-center">
                              <Cell row={row} planId={plan.id} />
                            </div>
                          </td>
                        ))}
                      </tr>
                    ))}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
