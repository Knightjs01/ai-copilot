"use client";

import * as React from "react";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  useCommercialSummary,
  useMyBilling,
  useStartBillingPortal,
  useStartCheckout,
} from "@/lib/queries/commercial";
import type { BillingPeriod, CompanyBillingStatus } from "@/lib/types";

const STATUS_LABEL: Record<CompanyBillingStatus, string> = {
  not_started: "Not started",
  active: "Active",
  past_due: "Past due",
  canceled: "Canceled",
};

const STATUS_VARIANT: Record<CompanyBillingStatus, BadgeProps["variant"]> = {
  not_started: "outline",
  active: "success",
  past_due: "warning",
  canceled: "danger",
};

// Real Stripe Checkout/Billing Portal only -- both are Stripe-hosted, redirect-based flows, so
// this component never touches a card number itself. Plan *assignment* stays admin-only (see the
// plan this shipped under); this only lets an already-assigned plan actually get paid for.
export function BillingCard() {
  const { data: billing, isLoading: billingLoading } = useMyBilling();
  const { data: summary } = useCommercialSummary();
  const [billingPeriod, setBillingPeriod] = React.useState<BillingPeriod>("monthly");
  const startCheckout = useStartCheckout();
  const startPortal = useStartBillingPortal();

  if (billingLoading || !billing) {
    return (
      <Card>
        <CardContent className="flex justify-center py-8">
          <Spinner className="h-5 w-5 text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  const handleSubscribe = () => {
    startCheckout.mutate(billingPeriod, {
      onSuccess: (data) => {
        window.location.href = data.checkout_url;
      },
    });
  };

  const handleManageBilling = () => {
    startPortal.mutate(undefined, {
      onSuccess: (data) => {
        window.location.href = data.portal_url;
      },
    });
  };

  const plan = summary?.plan;

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">Billing</h3>
          <Badge variant={STATUS_VARIANT[billing.status]}>{STATUS_LABEL[billing.status]}</Badge>
        </div>

        {plan && (
          <p className="text-sm text-muted-foreground">
            {plan.name} ·{" "}
            {billing.billing_period === "annual"
              ? `£${(plan.annual_price_pence / 100).toLocaleString()}/year`
              : `£${(plan.monthly_price_pence / 100).toLocaleString()}/month`}
          </p>
        )}

        {billing.status === "not_started" && (
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setBillingPeriod("monthly")}
                className={
                  billingPeriod === "monthly"
                    ? "rounded-full bg-foreground px-3 py-1.5 text-xs font-medium text-background"
                    : "rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
                }
              >
                Monthly
              </button>
              <button
                type="button"
                onClick={() => setBillingPeriod("annual")}
                className={
                  billingPeriod === "annual"
                    ? "rounded-full bg-foreground px-3 py-1.5 text-xs font-medium text-background"
                    : "rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
                }
              >
                Annual
              </button>
            </div>
            <Button
              variant="brand"
              size="sm"
              disabled={startCheckout.isPending}
              onClick={handleSubscribe}
            >
              {startCheckout.isPending ? "Redirecting…" : "Subscribe"}
            </Button>
          </div>
        )}

        {billing.status !== "not_started" && (
          <div className="flex justify-end">
            <Button
              variant="secondary"
              size="sm"
              disabled={startPortal.isPending}
              onClick={handleManageBilling}
            >
              {startPortal.isPending ? "Redirecting…" : "Manage billing"}
            </Button>
          </div>
        )}

        {billing.status === "past_due" && (
          <p className="text-xs text-warning-foreground">
            Your last payment failed. Update your payment method to keep your subscription active.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
