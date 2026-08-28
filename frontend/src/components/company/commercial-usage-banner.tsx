"use client";

import { ArrowUpRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { NEXT_PLAN, upgradeMailto } from "@/lib/commercial-upgrade";
import { useCommercialSummary } from "@/lib/queries/commercial";

// Real numbers only -- effective_limit null means unlimited (a Scale company with no override
// configured yet), never fabricated. Shown to every company user regardless of
// company.manage_settings, since "how many hiring processes are we running" is relevant beyond
// whoever happens to manage the profile.
//
// Deliberately two states, not a graduated "almost there" warning -- the master prompt's own
// upgrade-trigger examples fire exactly at the cap, not before ("don't aggressively interrupt").
// Under the limit: a quiet one-liner, no CTA. At the limit: a helpful, specific nudge with a real
// action (mailto -- there's no self-serve plan change for a company today).
export function CommercialUsageBanner() {
  const { data, isLoading } = useCommercialSummary();

  if (isLoading || !data) return null;

  const { plan, active_role_count, effective_limit } = data;
  const atLimit = effective_limit !== null && active_role_count >= effective_limit;

  if (!atLimit) {
    return (
      <Card>
        <CardContent className="flex flex-col gap-2 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            {plan && <Badge variant="outline">{plan.name}</Badge>}
            <p className="text-sm text-foreground">
              {effective_limit !== null ? (
                <>
                  <span className="font-semibold">{active_role_count}</span> of{" "}
                  <span className="font-semibold">{effective_limit}</span> active roles used
                </>
              ) : (
                <>
                  <span className="font-semibold">{active_role_count}</span> active role
                  {active_role_count === 1 ? "" : "s"} · unlimited on your plan
                </>
              )}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const next = plan ? NEXT_PLAN[plan.code] : null;
  const planName = plan?.name ?? "your plan";

  return (
    <Card className="border-brand/30 bg-brand/5">
      <CardContent className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1">
          <p className="text-sm font-semibold text-foreground">
            You&apos;re using all {effective_limit} active role{effective_limit === 1 ? "" : "s"}{" "}
            included in {planName}.
          </p>
          <p className="text-sm text-muted-foreground">
            {next
              ? `${next.name} gives your team more active roles, plus ${next.highlight}.`
              : "Contact us to increase your configured active-role limit."}
          </p>
        </div>
        <Button asChild variant="brand" size="sm" className="shrink-0">
          <a
            href={upgradeMailto(
              next ? `Upgrade to ${next.name}` : `Increase active-role limit for ${planName}`
            )}
          >
            {next ? `Upgrade to ${next.name}` : "Talk to Phantom"}
            <ArrowUpRight className="h-3.5 w-3.5" />
          </a>
        </Button>
      </CardContent>
    </Card>
  );
}
