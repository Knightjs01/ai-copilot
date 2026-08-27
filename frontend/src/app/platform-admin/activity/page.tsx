"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { History } from "lucide-react";

import { Badge } from "@/components/ui/badge";
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
  "company_profile.approved": "Approved profile",
  "company_profile.rejected": "Rejected profile",
  "tenant_data.purged": "Purged all tenant data",
};

function describeEntry(entry: PlatformAdminAuditLogEntry): string {
  const companyName = entry.extra_data?.company_name;
  return typeof companyName === "string" ? companyName : entry.target_type;
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
  const { data: entries, isLoading } = useAuditLog();

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

      {!isLoading && entries?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <History className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No admin activity yet.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && entries && entries.length > 0 && (
        <div className="flex flex-col gap-3">
          {entries.map((entry) => (
            <EntryRow key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}
