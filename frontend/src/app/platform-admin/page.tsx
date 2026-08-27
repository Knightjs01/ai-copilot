"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ShieldAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { StatTile } from "@/components/ui/stat-tile";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { useDashboardStats } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";

export default function PlatformAdminDashboardPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
  const { data: stats, isLoading } = useDashboardStats();

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

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          <StatTile label="Pending" value={stats.pending_requests} />
          <StatTile label="Approved" value={stats.approved_requests} />
          <StatTile label="Rejected" value={stats.rejected_requests} />
          <StatTile label="Active companies" value={stats.active_companies} />
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
