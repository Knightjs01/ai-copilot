import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { COMPANY_PLANS, type BillingPeriod } from "@/lib/pricing-config";

const TALENT_MEMORY_LABEL: Record<string, string> = {
  not_included: "Not included",
  included: "Included (Preview)",
  included_extended: "Included, extended (Preview)",
};

const ANALYTICS_LABEL: Record<string, string> = {
  basic: "Basic analytics",
  advanced: "Advanced analytics",
  phantom_intelligence: "Phantom Intelligence (Preview)",
};

function formatPrice(amount: number | null): string {
  if (amount === null) return "Custom";
  if (amount === 0) return "£0";
  return `£${amount.toLocaleString("en-GB")}`;
}

export function CompanyPlansSection({
  billingPeriod,
  onBillingPeriodChange,
}: {
  billingPeriod: BillingPeriod;
  onBillingPeriodChange: (period: BillingPeriod) => void;
}) {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Start free. Scale when Phantom becomes part of your hiring engine.
          </h2>
        </div>

        <div className="mt-8 flex flex-col items-center gap-2">
          <PillToggleGroup
            options={[
              { value: "annual", label: "Annual" },
              { value: "monthly", label: "Monthly" },
            ]}
            value={billingPeriod}
            onChange={onBillingPeriodChange}
          />
          {billingPeriod === "annual" && (
            <span className="text-xs font-medium text-success">Save 20% with annual billing</span>
          )}
        </div>

        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {COMPANY_PLANS.map((plan) => {
            const price =
              billingPeriod === "annual" ? plan.price.annualMonthlyEquivalent : plan.price.monthly;
            return (
              <div
                key={plan.id}
                className={`relative flex flex-col gap-4 rounded-2xl border bg-card p-6 shadow-sm shadow-slate-900/[0.03] ${
                  plan.mostPopular ? "border-brand/40 ring-1 ring-brand/20" : "border-border"
                }`}
              >
                {plan.mostPopular && (
                  <Badge variant="info" className="absolute -top-3 left-6">
                    Most popular
                  </Badge>
                )}
                <div>
                  <h3 className="text-lg font-semibold text-foreground">{plan.name}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">{plan.tagline}</p>
                </div>

                <div className="flex items-end gap-1.5">
                  <span className="text-3xl font-semibold tracking-tight text-foreground">
                    {formatPrice(price)}
                  </span>
                  {price !== null && price > 0 && (
                    <span className="pb-1 text-xs text-muted-foreground">
                      /month{billingPeriod === "annual" ? ", billed annually" : ""}
                    </span>
                  )}
                </div>

                <p className="text-xs text-muted-foreground">{plan.idealFor}</p>

                <div className="flex flex-col gap-1 border-y border-border py-3 text-xs text-muted-foreground">
                  <p>{plan.roles}</p>
                  <p>{plan.seats}</p>
                  <p>{plan.aiAllowance.label}</p>
                  <p>{TALENT_MEMORY_LABEL[plan.talentMemory]}</p>
                  <p>{ANALYTICS_LABEL[plan.analyticsLevel]}</p>
                </div>

                <ul className="flex flex-1 flex-col gap-2">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" />
                      <span className="text-xs leading-relaxed text-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button asChild variant={plan.mostPopular ? "brand" : "secondary"} className="mt-2">
                  <Link href={plan.cta.href}>{plan.cta.label}</Link>
                </Button>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
