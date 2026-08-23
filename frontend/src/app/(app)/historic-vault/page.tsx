"use client";

import { ShieldAlert, ShieldCheck } from "lucide-react";

import { RelativeTime } from "@/components/relative-time";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatTile } from "@/components/ui/stat-tile";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useAuth } from "@/lib/auth-context";
import { useHistoricVaultOverview } from "@/lib/queries/historic-vault";

function formatAuditAction(action: string): string {
  const [subject = "", ...rest] = action.split(".");
  const verb = rest.join(" ").replace(/_/g, " ");
  return `${subject.charAt(0).toUpperCase()}${subject.slice(1)}: ${verb}`;
}

export default function HistoricVaultPage() {
  const { hasPermission } = useAuth();
  const canView = hasPermission("historic_vault.view");
  const { data, isLoading } = useHistoricVaultOverview();

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Project Vault is Admin-only</p>
        <p className="max-w-xs text-sm text-muted-foreground">
          Ask an Owner or Admin on your team for access.
        </p>
      </div>
    );
  }

  if (isLoading || !data) {
    return (
      <div className="flex flex-col gap-8">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-16 w-full" />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  return (
    <TooltipProvider>
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Project Vault</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Long-term record of purged hiring projects and the company audit trail.
        </p>
      </div>

      <div className="flex items-center gap-2 rounded-xl border border-brand/20 bg-brand/5 px-4 py-3">
        <ShieldCheck className="h-4 w-4 shrink-0 text-brand" />
        <p className="text-sm text-foreground">
          Admin+ governance view. Purge certificates and audit entries here outlive the projects
          and candidates they describe. Every burn is recorded permanently.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatTile label="Purged projects" value={data.purged_project_count} />
        <StatTile label="Audit entries shown" value={data.recent_audit_entries.length} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Purged projects</CardTitle>
        </CardHeader>
        <CardContent>
          {data.purged_projects.length === 0 ? (
            <p className="text-sm text-muted-foreground">No projects have been purged yet.</p>
          ) : (
            <div className="flex flex-col divide-y divide-border">
              {data.purged_projects.map((record) => (
                <div key={record.id} className="flex flex-col gap-1.5 py-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-foreground">
                      {record.project_title}
                    </span>
                    <RelativeTime date={record.purged_at} className="text-xs text-muted-foreground" />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {record.candidate_count} candidate{record.candidate_count === 1 ? "" : "s"} ·
                    purged by {record.purged_by_email}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Destroyed: {record.data_categories_destroyed.join(", ")}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Audit trail</CardTitle>
        </CardHeader>
        <CardContent>
          {data.recent_audit_entries.length === 0 ? (
            <p className="text-sm text-muted-foreground">No audit activity yet.</p>
          ) : (
            <div className="flex flex-col divide-y divide-border">
              {data.recent_audit_entries.map((entry) => (
                <div key={entry.id} className="flex items-center justify-between gap-3 py-3">
                  <span className="text-sm text-foreground">{formatAuditAction(entry.action)}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground">
                      {entry.actor_email ?? "System"}
                    </span>
                    <RelativeTime date={entry.created_at} className="text-xs text-muted-foreground" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
    </TooltipProvider>
  );
}
