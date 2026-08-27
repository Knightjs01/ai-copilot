"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Building2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { ProfileReviewDialog } from "@/components/platform-admin/profile-review-dialog";
import {
  useAllCompanies,
  useReactivateCompany,
  useSuspendCompany,
} from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { COMPANY_PROFILE_STATUS_LABEL, COMPANY_PROFILE_STATUS_VARIANT } from "@/lib/status-display";
import type { AdminCompanySummary } from "@/lib/types";

function CompanyRow({ company }: { company: AdminCompanySummary }) {
  const suspend = useSuspendCompany();
  const reactivate = useReactivateCompany();
  const isPending = suspend.isPending || reactivate.isPending;

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-foreground">{company.name}</h3>
            <Badge variant={company.status === "suspended" ? "danger" : "success"}>
              {company.status}
            </Badge>
            <Badge variant={COMPANY_PROFILE_STATUS_VARIANT[company.profile_status]}>
              {COMPANY_PROFILE_STATUS_LABEL[company.profile_status]}
            </Badge>
            {!company.is_verified_domain && <Badge variant="outline">unverified domain</Badge>}
          </div>
          <p className="text-sm text-muted-foreground">{company.email_domain}</p>
          <p className="text-xs text-muted-foreground">
            {company.user_count} member{company.user_count === 1 ? "" : "s"} · created{" "}
            {new Date(company.created_at).toLocaleDateString()}
          </p>
        </div>

        {(suspend.isError || reactivate.isError) && (
          <p className="text-sm font-medium text-danger">Couldn&apos;t save. Try again.</p>
        )}

        <div className="flex shrink-0 gap-2">
          {company.profile_status === "pending_review" && (
            <ProfileReviewDialog companyId={company.id} companyName={company.name} />
          )}
          {company.status === "suspended" ? (
            <Button
              type="button"
              variant="brand"
              size="sm"
              onClick={() => reactivate.mutate(company.id)}
              disabled={isPending}
            >
              {reactivate.isPending ? "Reactivating…" : "Reactivate"}
            </Button>
          ) : (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => suspend.mutate(company.id)}
              disabled={isPending}
            >
              {suspend.isPending ? "Suspending…" : "Suspend"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function PlatformAdminCompaniesPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading } = usePlatformAdminAuth();
  const { data: companies, isLoading } = useAllCompanies();

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

      {!isLoading && companies?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <Building2 className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No companies yet.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && companies && companies.length > 0 && (
        <div className="flex flex-col gap-3">
          {companies.map((company) => (
            <CompanyRow key={company.id} company={company} />
          ))}
        </div>
      )}
    </div>
  );
}
