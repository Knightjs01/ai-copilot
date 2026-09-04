"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { History } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { useAuditLog } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import type { PlatformAdminAuditLogEntry } from "@/lib/types";

const ACTION_LABEL: Record<string, string> = {
  "access_request.approved": "Approved request",
  "access_request.rejected": "Rejected request",
  "access_request.info_requested": "Requested info",
  "company.suspended": "Suspended company",
  "company.reactivated": "Reactivated company",
  "company.verified_employer_set": "Set verified-employer status",
  "company.created": "Created company",
  "company.plan_changed": "Changed commercial plan",
  "company_profile.approved": "Approved profile",
  "company_profile.rejected": "Rejected profile",
  "company_user.admin_invited": "Invited company user",
  "shadow_job.approved": "Approved job",
  "shadow_job.rejected": "Rejected job",
  "admin.created": "Created admin account",
  "admin.password_reset": "Reset admin password",
  "admin.mfa_enabled": "Enabled MFA",
  "admin.mfa_disabled": "Disabled MFA",
  "admin.step_up_verified": "Verified step-up",
  "tenant_data.purged": "Purged all tenant data",
};

const PAGE_SIZE = 50;

function describeEntry(entry: PlatformAdminAuditLogEntry): string {
  const companyName = entry.extra_data?.company_name;
  if (typeof companyName === "string") return companyName;
  const email = entry.extra_data?.email;
  if (typeof email === "string") return email;
  return entry.target_type;
}

function EntryRow({ entry }: { entry: PlatformAdminAuditLogEntry }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1 py-4">
        <div className="flex items-center gap-2">
          <Badge variant="outline">{ACTION_LABEL[entry.action] ?? entry.action}</Badge>
          <p className="text-sm font-medium text-foreground">{describeEntry(entry)}</p>
        </div>
        <p className="text-xs text-muted-foreground">
          {new Date(entry.created_at).toLocaleString()}
        </p>
      </CardContent>
    </Card>
  );
}

export default function PlatformAdminActivityPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading } = usePlatformAdminAuth();
  const [actionFilter, setActionFilter] = React.useState("");
  const [page, setPage] = React.useState(1);
  const { data, isLoading } = useAuditLog({
    action: actionFilter || undefined,
    page,
    pageSize: PAGE_SIZE,
  });
  const entries = data?.items ?? [];
  const total = data?.total ?? 0;
  const hasNextPage = page * PAGE_SIZE < total;

  React.useEffect(() => {
    if (!authLoading && !admin) router.push("/platform-admin/login");
  }, [authLoading, admin, router]);

  React.useEffect(() => {
    setPage(1);
  }, [actionFilter]);

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

      <div className="flex items-center justify-between gap-3">
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="rounded-lg border border-border bg-card px-3 py-1.5 text-sm text-foreground"
        >
          <option value="">All actions</option>
          {Object.entries(ACTION_LABEL).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {!isLoading && (
        <p className="text-xs text-muted-foreground">
          Showing {entries.length === 0 ? 0 : (page - 1) * PAGE_SIZE + 1}–
          {(page - 1) * PAGE_SIZE + entries.length} of {total} entries
        </p>
      )}

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && entries.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <History className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No admin activity yet.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && entries.length > 0 && (
        <div className="flex flex-col gap-3">
          {entries.map((entry) => (
            <EntryRow key={entry.id} entry={entry} />
          ))}
        </div>
      )}

      {!isLoading && total > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </Button>
          <span className="text-xs text-muted-foreground">Page {page}</span>
          <Button
            variant="secondary"
            size="sm"
            disabled={!hasNextPage}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
