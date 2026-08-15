"use client";

import * as React from "react";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";

import { RevealIdentityDialog } from "@/components/candidate/reveal-identity-dialog";
import { RelativeTime } from "@/components/relative-time";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatTile } from "@/components/ui/stat-tile";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useProjectVault, useVaultDashboard } from "@/lib/queries/identity-vault";
import { CANDIDATE_STATUS_LABEL, CANDIDATE_STATUS_VARIANT } from "@/lib/status-display";
import type { VaultListItem } from "@/lib/types";

const columnHelper = createColumnHelper<VaultListItem>();

export function IdentityVaultTab({ projectId }: { projectId: string }) {
  const { data: stats, isLoading: statsLoading } = useVaultDashboard(projectId);
  const { data: vaultItems, isLoading: itemsLoading } = useProjectVault(projectId);
  const [sorting, setSorting] = React.useState<SortingState>([]);

  const columns = React.useMemo(
    () => [
      columnHelper.accessor("callsign", {
        header: "Callsign",
        cell: (info) => (
          <Link
            href={`/projects/${projectId}/candidates/${info.row.original.candidate_id}`}
            className="font-medium text-foreground hover:underline"
          >
            {info.getValue()}
          </Link>
        ),
      }),
      columnHelper.accessor("candidate_ref", {
        header: "Candidate ID",
        cell: (info) => <span className="text-muted-foreground">{info.getValue()}</span>,
      }),
      columnHelper.accessor("status", {
        header: "Status",
        cell: (info) => (
          <Badge variant={CANDIDATE_STATUS_VARIANT[info.getValue()]}>
            {CANDIDATE_STATUS_LABEL[info.getValue()]}
          </Badge>
        ),
      }),
      columnHelper.accessor("vault_populated", {
        header: "Vault",
        cell: (info) =>
          info.getValue() ? (
            <Badge variant="success">Filled</Badge>
          ) : (
            <span className="text-xs text-muted-foreground">Not yet filled</span>
          ),
      }),
      columnHelper.display({
        id: "actions",
        header: "",
        cell: (info) => (
          <div className="flex justify-end">
            <RevealIdentityDialog candidateId={info.row.original.candidate_id} />
          </div>
        ),
      }),
    ],
    [projectId]
  );

  const table = useReactTable({
    data: vaultItems ?? [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

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
        <CardContent className={vaultItems.length === 0 ? undefined : "p-0"}>
          {vaultItems.length === 0 ? (
            <p className="text-sm text-muted-foreground">No candidates in this project yet.</p>
          ) : (
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead
                        key={header.id}
                        sortable={header.column.getCanSort()}
                        sortDirection={header.column.getIsSorted()}
                        onSort={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.map((row) => (
                  <TableRow key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
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
