"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { StatTile } from "@/components/ui/stat-tile";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { useActionQueue, useDashboardStats } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import type { ActionQueueItem, ActionQueueItemType } from "@/lib/types";

const ACTION_QUEUE_GROUP_LABEL: Record<ActionQueueItemType, { one: string; many: string }> = {
  access_request: { one: "pending access request", many: "pending access requests" },
  job_review: { one: "job awaiting review", many: "jobs awaiting review" },
  profile_review: {
    one: "company profile awaiting review",
    many: "company profiles awaiting review",
  },
};

function groupByType(items: ActionQueueItem[]): Map<ActionQueueItemType, ActionQueueItem[]> {
  const groups = new Map<ActionQueueItemType, ActionQueueItem[]>();
  for (const item of items) {
    const existing = groups.get(item.type);
    if (existing) {
      existing.push(item);
    } else {
      groups.set(item.type, [item]);
    }
  }
  return groups;
}

export default function PlatformAdminDashboardPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
  const { data: stats, isLoading } = useDashboardStats();
  const { data: actionQueue, isLoading: isActionQueueLoading } = useActionQueue();

  React.useEffect(() => {
    if (!authLoading && !admin) router.push("/platform-admin/login");
  }, [authLoading, admin, router]);

  if (authLoading || !admin) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  const groupedQueue = actionQueue ? groupByType(actionQueue) : null;

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile label="Active companies" value={stats.active_companies} />
          <StatTile label="Active roles" value={stats.active_role_count} />
          <StatTile label="Verified candidates" value={stats.verified_candidate_count} />
          <StatTile label="Applications" value={stats.application_count} />
          <StatTile label="Pending" value={stats.pending_requests} />
          <StatTile label="Approved" value={stats.approved_requests} />
          <StatTile label="Rejected" value={stats.rejected_requests} />
          <StatTile label="Suspended" value={stats.suspended_companies} />
        </div>
      )}

      {stats && stats.pending_requests > 0 && (
        <Card>
          <CardContent className="flex flex-col gap-3 py-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-col gap-0.5">
              <p className="text-sm font-medium text-foreground">
                {stats.pending_requests} pending request{stats.pending_requests === 1 ? "" : "s"}
              </p>
              <p className="text-sm text-muted-foreground">
                Waiting for a decision — approve, reject, or ask for more info.
              </p>
            </div>
            <Button asChild size="sm">
              <Link href="/platform-admin/requests">Review requests</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Needs Your Attention</CardTitle>
          <CardDescription>Real items waiting on a decision, oldest and largest first.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {isActionQueueLoading && (
            <div className="flex justify-center py-6">
              <Spinner className="h-5 w-5 text-muted-foreground" />
            </div>
          )}

          {groupedQueue && groupedQueue.size === 0 && (
            <p className="py-2 text-sm text-muted-foreground">
              Nothing needs your attention right now.
            </p>
          )}

          {groupedQueue &&
            Array.from(groupedQueue.entries()).map(([type, items]) => {
              const label = ACTION_QUEUE_GROUP_LABEL[type];
              const hasAging = items.some((item) => item.priority === "high");
              const reviewUrl = items[0]?.url ?? "/platform-admin";
              return (
                <div
                  key={type}
                  className="flex flex-col gap-2 rounded-lg border border-border px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-foreground">
                      {items.length} {items.length === 1 ? label.one : label.many}
                    </p>
                    {hasAging && (
                      <Badge variant="warning">
                        {items.filter((item) => item.priority === "high").length} aging 48h+
                      </Badge>
                    )}
                  </div>
                  <Button asChild size="sm" variant="secondary">
                    <Link href={reviewUrl}>Review</Link>
                  </Button>
                </div>
              );
            })}
        </CardContent>
      </Card>

      {hasPermission("danger_zone.purge") && (
        <Card className="border-danger/30">
          <CardHeader>
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-danger" />
              <CardTitle>Danger Zone</CardTitle>
            </div>
            <CardDescription>
              Irreversible platform-wide actions. Your own platform-admin login is never affected.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="danger" size="sm">
              <Link href="/platform-admin/danger-zone">Open Danger Zone</Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
