"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ShieldAlert } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { PurgeAllDataDialog } from "@/components/platform-admin/purge-all-data-dialog";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";

export default function PlatformAdminDangerZonePage() {
  const router = useRouter();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();

  React.useEffect(() => {
    if (authLoading) return;
    if (!admin) router.push("/platform-admin/login");
    else if (!hasPermission("danger_zone.purge")) router.push("/platform-admin");
  }, [authLoading, admin, hasPermission, router]);

  if (authLoading || !admin || !hasPermission("danger_zone.purge")) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />

      <Card className="border-danger/30">
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-danger" />
            <CardTitle>Purge all tenant data</CardTitle>
          </div>
          <CardDescription>
            Deletes every company, company user, candidate, Passport, project, application, and
            job on the platform — a genuinely clean slate. Your platform-admin logins,
            permissions, and this action&apos;s own audit trail are never touched.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PurgeAllDataDialog />
        </CardContent>
      </Card>
    </div>
  );
}
