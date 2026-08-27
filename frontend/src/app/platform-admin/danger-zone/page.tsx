"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldAlert, ShieldOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { PurgeAllDataDialog } from "@/components/platform-admin/purge-all-data-dialog";
import { PlatformAdminStepUpDialog } from "@/components/platform-admin/step-up-dialog";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";

export default function PlatformAdminDangerZonePage() {
  const router = useRouter();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
  const [stepUpToken, setStepUpToken] = React.useState<string | null>(null);
  const [stepUpOpen, setStepUpOpen] = React.useState(true);

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

  // No page content at all without MFA -- not just the purge button. Set up MFA on the
  // Security page first, then come back.
  if (!admin.mfa_enabled) {
    return (
      <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
        <PlatformAdminNav admin={admin} />
        <Card className="border-danger/30">
          <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
            <ShieldOff className="h-6 w-6 text-danger" />
            <p className="text-sm font-medium text-foreground">
              Set up multi-factor authentication to access the Danger Zone
            </p>
            <p className="max-w-xs text-sm text-muted-foreground">
              This page is never reachable without it, regardless of role.
            </p>
            <Button asChild size="sm">
              <Link href="/platform-admin/security">Set up MFA</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // MFA is enabled but this page-visit hasn't stepped up yet -- the step-up dialog stands in for
  // the page content entirely; cancelling it routes away rather than leaving the page reachable.
  if (!stepUpToken) {
    return (
      <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
        <PlatformAdminNav admin={admin} />
        <PlatformAdminStepUpDialog
          open={stepUpOpen}
          onOpenChange={(open) => {
            setStepUpOpen(open);
            if (!open) router.push("/platform-admin");
          }}
          title="Confirm it's you"
          description="Re-enter your password and authenticator code to access the Danger Zone."
          onVerified={(token) => setStepUpToken(token)}
        />
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
          <PurgeAllDataDialog stepUpToken={stepUpToken} />
        </CardContent>
      </Card>
    </div>
  );
}
