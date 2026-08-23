"use client";

import * as React from "react";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { annualSavingsPercent, COMPANY_PLANS, type BillingPeriod } from "@/lib/pricing-config";

const CARD_FEATURE_COUNT = 8;

export function CompanyPlansSection() {
  const [billingPeriod, setBillingPeriod] = React.useState<BillingPeriod>("annual");

  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="flex flex-col items-center gap-2">
          <PillToggleGroup
            options={[
              { value: "annual", label: "Annual" },
              { value: "monthly", label: "Monthly" },
            ]}
            value={billingPeriod}
            onChange={setBillingPeriod}
          />
        </div>

        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {COMPANY_PLANS.map((plan) => {
            const price = billingPeriod === "annual" ? plan.price.annual : plan.price.monthly;
            const savings = annualSavingsPercent(plan);
            const cardFeatures = plan.features.slice(0, CARD_FEATURE_COUNT);

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

                <div className="flex flex-col gap-1">
                  <div className="flex items-end gap-1.5">
                    <span className="text-3xl font-semibold tracking-tight text-foreground">
                      {price === null
                        ? "Custom"
                        : billingPeriod === "annual"
                          ? `£${price.toLocaleString("en-GB")}`
                          : `£${price.toLocaleString("en-GB")}`}
                    </span>
                    {price !== null && (
                      <span className="pb-1 text-xs text-muted-foreground">
                        /{billingPeriod === "annual" ? "year" : "month"}
                      </span>
                    )}
                  </div>
                  {billingPeriod === "annual" && savings !== null && savings > 0 && (
                    <span className="text-xs font-medium text-success">Save ~{savings}%</span>
                  )}
                </div>

                <ul className="flex flex-1 flex-col gap-2">
                  {cardFeatures.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" />
                      <span className="text-xs leading-relaxed text-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>

                <a
                  href="#compare-plans"
                  className="text-xs font-medium text-brand hover:underline"
                >
                  View all features
                </a>

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
