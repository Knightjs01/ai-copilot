"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { CompanyOnboardingWizard } from "@/components/platform-admin/company-onboarding-wizard";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";

export default function NewCompanyOnboardingPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();

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
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />
      {hasPermission("companies.create") ? (
        <CompanyOnboardingWizard />
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <p className="text-sm text-muted-foreground">
              You don&apos;t have permission to onboard a new company.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
