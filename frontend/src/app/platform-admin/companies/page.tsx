"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { BadgeCheck, Building2, Plus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { useAllCompanies } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { COMPANY_PROFILE_STATUS_LABEL, COMPANY_PROFILE_STATUS_VARIANT } from "@/lib/status-display";
import type { AdminCompanySummary } from "@/lib/types";

function CompanyRow({ company }: { company: AdminCompanySummary }) {
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
            {company.is_verified_employer && (
              <Badge variant="gold">
                <BadgeCheck className="h-3 w-3" />
                Verified employer
              </Badge>
            )}
            {company.commercial_plan_code && (
              <Badge variant="outline">
                {company.commercial_plan_code.charAt(0).toUpperCase() +
                  company.commercial_plan_code.slice(1)}
                {company.active_role_limit_override !== null &&
                  ` (${company.active_role_limit_override} override)`}
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{company.email_domain}</p>
          <p className="text-xs text-muted-foreground">
            {company.user_count} member{company.user_count === 1 ? "" : "s"} · created{" "}
            {new Date(company.created_at).toLocaleDateString()}
          </p>
        </div>

        <Link
          href={`/platform-admin/companies/${company.id}`}
          className="shrink-0 text-sm font-medium text-brand hover:underline"
        >
          View details →
        </Link>
      </CardContent>
    </Card>
  );
}

export default function PlatformAdminCompaniesPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
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

      {hasPermission("companies.create") && (
        <div className="flex justify-end">
          <Button asChild size="sm">
            <Link href="/platform-admin/companies/new">
              <Plus className="h-3.5 w-3.5" />
              New company
            </Link>
          </Button>
        </div>
      )}

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
