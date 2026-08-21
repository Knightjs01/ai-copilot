"use client";

import { ActionItemRow } from "@/components/dashboard/action-item-row";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useProjectDashboardStats } from "@/lib/queries/dashboard";
import { useProjectAnalytics } from "@/lib/queries/analytics";
import { FIT_RATING_VARIANT, PRESCREEN_OUTCOME_LABEL, PRESCREEN_OUTCOME_VARIANT } from "@/lib/status-display";
import type { FitRating, PrescreenOutcome } from "@/lib/types";

// Two real, honest pillars -- pipeline strength and candidate quality. Deliberately no
// composite numeric "health score": there's no real signal (LLM judgment or otherwise)
// backing a single fabricated number, matching this codebase's standing discipline against
// invented scores/tiers (no fake match percentages, no fake verification tiers).
export function RoleHealthCard({ projectId }: { projectId: string }) {
  const { data: dashboard, isLoading: dashboardLoading } = useProjectDashboardStats(projectId);
  const { data: analytics, isLoading: analyticsLoading } = useProjectAnalytics(projectId);

  if (dashboardLoading || analyticsLoading || !dashboard || !analytics) {
    return (
      <Card>
        <CardContent className="flex justify-center py-10">
          <Spinner className="h-5 w-5 text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (analytics.total_candidates === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Role Health</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Add candidates to this project to see its pipeline and quality signals.
          </p>
        </CardContent>
      </Card>
    );
  }

  const fitRatingEntries = Object.entries(analytics.fit_rating_breakdown) as [FitRating, number][];
  const prescreenOutcomeEntries = Object.entries(analytics.prescreen_outcome_breakdown) as [
    PrescreenOutcome,
    number,
  ][];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Role Health</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        <div>
          <h3 className="mb-2 text-sm font-medium text-foreground">Pipeline strength</h3>
          {dashboard.action_items.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No open gaps — this role&apos;s pipeline is fully up to date.
            </p>
          ) : (
            <div className="flex flex-col gap-0.5">
              {dashboard.action_items.map((item, index) => (
                <ActionItemRow
                  key={`${item.type}-${item.candidate_id ?? item.project_id}-${index}`}
                  item={item}
                />
              ))}
            </div>
          )}
        </div>

        <div>
          <h3 className="mb-2 text-sm font-medium text-foreground">Candidate quality</h3>
          {fitRatingEntries.length === 0 && prescreenOutcomeEntries.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No fit assessments or pre-screen outcomes recorded yet.
            </p>
          ) : (
            <div className="flex flex-col gap-3">
              {fitRatingEntries.length > 0 && (
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-muted-foreground">AI fit rating:</span>
                  {fitRatingEntries.map(([rating, count]) => (
                    <Badge key={rating} variant={FIT_RATING_VARIANT[rating]}>
                      {rating} · {count}
                    </Badge>
                  ))}
                </div>
              )}
              {prescreenOutcomeEntries.length > 0 && (
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-muted-foreground">Pre-screen outcome:</span>
                  {prescreenOutcomeEntries.map(([outcome, count]) => (
                    <Badge key={outcome} variant={PRESCREEN_OUTCOME_VARIANT[outcome]}>
                      {PRESCREEN_OUTCOME_LABEL[outcome]} · {count}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
