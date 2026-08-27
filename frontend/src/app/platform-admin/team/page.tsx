"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Users } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { CreateAdminDialog } from "@/components/platform-admin/create-admin-dialog";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { useAdmins } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { PLATFORM_ADMIN_ROLE_LABEL, PLATFORM_ADMIN_ROLE_VARIANT } from "@/lib/status-display";
import type { PlatformAdminRoleName } from "@/lib/types";

export default function PlatformAdminTeamPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
  const { data: admins, isLoading } = useAdmins();

  React.useEffect(() => {
    if (authLoading) return;
    if (!admin) router.push("/platform-admin/login");
    else if (!hasPermission("admins.manage")) router.push("/platform-admin");
  }, [authLoading, admin, hasPermission, router]);

  if (authLoading || !admin || !hasPermission("admins.manage")) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">Phantom staff with platform-admin access.</p>
        <CreateAdminDialog />
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && admins?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <Users className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No other admins yet.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && admins && admins.length > 0 && (
        <div className="flex flex-col gap-3">
          {admins.map((a) => (
            <Card key={a.id}>
              <CardContent className="flex items-center justify-between gap-3 py-4">
                <div className="flex items-center gap-3">
                  <Avatar name={a.full_name} className="h-8 w-8 text-xs" />
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-foreground">{a.full_name}</span>
                    <span className="text-xs text-muted-foreground">{a.email}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {a.roles.map((role) => (
                    <Badge
                      key={role}
                      variant={PLATFORM_ADMIN_ROLE_VARIANT[role as PlatformAdminRoleName]}
                    >
                      {PLATFORM_ADMIN_ROLE_LABEL[role as PlatformAdminRoleName] ?? role}
                    </Badge>
                  ))}
                  {!a.is_active && <Badge variant="outline">Inactive</Badge>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
