"use client";

import Link from "next/link";
import { ShieldCheck } from "lucide-react";

import { RevealIdentityDialog } from "@/components/candidate/reveal-identity-dialog";
import { RelativeTime } from "@/components/relative-time";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatTile } from "@/components/ui/stat-tile";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useProjectVault, useVaultDashboard } from "@/lib/queries/identity-vault";
import { CANDIDATE_STATUS_LABEL } from "@/lib/status-display";

export function IdentityVaultTab({ projectId }: { projectId: string }) {
  const { data: stats, isLoading: statsLoading } = useVaultDashboard(projectId);
  const { data: vaultItems, isLoading: itemsLoading } = useProjectVault(projectId);

  if (statsLoading || itemsLoading || !stats || !vaultItems) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-16 w-full" />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  return (
    <TooltipProvider>
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-2 rounded-xl border border-brand/20 bg-brand/5 px-4 py-3">
        <ShieldCheck className="h-4 w-4 shrink-0 text-brand" />
        <p className="text-sm text-foreground">
          Owner-only governance view. This tab is never visible to other roles, and never exposes
          candidate identity directly. Only Reveal actions surface decrypted data, and every one
          is audited below.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatTile label="Total candidates" value={stats.total_candidates} />
        <StatTile label="Active vault records" value={stats.active_vault_records} />
        <StatTile label="Identity reveal events" value={stats.reveal_event_count} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Candidate identity vault</CardTitle>
        </CardHeader>
        <CardContent>
          {vaultItems.length === 0 ? (
            <p className="text-sm text-muted-foreground">No candidates in this project yet.</p>
          ) : (
            <div className="flex flex-col divide-y divide-border">
              {vaultItems.map((item) => (
                <div
                  key={item.candidate_id}
                  className="flex items-center justify-between gap-3 py-3"
                >
                  <div className="flex items-center gap-3">
                    <Link
                      href={`/projects/${projectId}/candidates/${item.candidate_id}`}
                      className="text-sm font-medium text-foreground hover:underline"
                    >
                      {item.callsign}
                    </Link>
                    <span className="text-xs text-muted-foreground">{item.candidate_ref}</span>
                    <Badge variant="neutral">{CANDIDATE_STATUS_LABEL[item.status]}</Badge>
                    {!item.vault_populated && (
                      <span className="text-xs text-muted-foreground">Vault not yet filled</span>
                    )}
                  </div>
                  <RevealIdentityDialog candidateId={item.candidate_id} />
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
          {stats.recent_reveals.length === 0 ? (
            <p className="text-sm text-muted-foreground">No identity reveals yet.</p>
          ) : (
            <div className="flex flex-col divide-y divide-border">
              {stats.recent_reveals.map((event) => (
                <div key={event.id} className="flex flex-col gap-0.5 py-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-foreground">
                      {event.actor_email} viewed identity · {event.callsign}
                    </span>
                    <RelativeTime date={event.revealed_at} className="text-xs text-muted-foreground" />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Reason: {event.reason}
                    {event.duration_seconds != null && ` · Viewed for ${event.duration_seconds}s`}
                  </p>
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
