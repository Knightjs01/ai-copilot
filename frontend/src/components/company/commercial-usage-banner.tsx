"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useCommercialSummary } from "@/lib/queries/commercial";

// Real numbers only -- effective_limit null means unlimited (a Scale company with no override
// configured yet), never fabricated. Shown to every company user regardless of
// company.manage_settings, since "how many hiring processes are we running" is relevant beyond
// whoever happens to manage the profile.
export function CommercialUsageBanner() {
  const { data, isLoading } = useCommercialSummary();

  if (isLoading || !data) return null;

  const { plan, active_role_count, effective_limit } = data;
  const atLimit = effective_limit !== null && active_role_count >= effective_limit;

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
        {atLimit && (
          <p className="text-sm font-medium text-danger">
            You&apos;ve reached your plan&apos;s active-role limit. Close a role or upgrade to
            create another.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
