"use client";

import { formatDistanceToNow } from "date-fns";
import { ShieldAlert, ShieldCheck } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";
import { useHistoricVaultOverview } from "@/lib/queries/historic-vault";

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col gap-1 rounded-xl border border-border bg-white px-4 py-3">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <span className="text-xl font-semibold tracking-tight text-foreground">{value}</span>
    </div>
  );
}

function formatAuditAction(action: string): string {
  const [subject = "", ...rest] = action.split(".");
  const verb = rest.join(" ").replace(/_/g, " ");
  return `${subject.charAt(0).toUpperCase()}${subject.slice(1)} — ${verb}`;
}

export default function HistoricVaultPage() {
  const { hasPermission } = useAuth();
  const canView = hasPermission("historic_vault.view");
  const { data, isLoading } = useHistoricVaultOverview();

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Historic Vault is Admin-only</p>
        <p className="max-w-xs text-sm text-muted-foreground">
          Ask an Owner or Admin on your team for access.
        </p>
      </div>
    );
  }

  if (isLoading || !data) {
    return (
      <div className="flex justify-center py-24">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Historic Vault</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Long-term record of purged hiring projects and the company audit trail.
        </p>
      </div>

      <div className="flex items-center gap-2 rounded-xl border border-brand/20 bg-brand/5 px-4 py-3">
        <ShieldCheck className="h-4 w-4 shrink-0 text-brand" />
        <p className="text-sm text-foreground">
          Admin+ governance view. Purge certificates and audit entries here outlive the projects
          and candidates they describe — every burn is recorded permanently.
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
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(record.purged_at), { addSuffix: true })}
                    </span>
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
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
