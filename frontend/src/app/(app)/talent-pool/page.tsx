"use client";

import * as React from "react";
import { Search, ShieldAlert } from "lucide-react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";

import { CandidateSearchResultCard } from "@/components/candidate-search/candidate-search-result-card";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/lib/auth-context";
import { useTalentPoolMatches } from "@/lib/queries/candidate-search";
import { useMyShadowJobs } from "@/lib/queries/shadow-jobs";
import { useCompanyTalentPool } from "@/lib/queries/talent-pool";
import { TALENT_POOL_SCOPE_LABEL } from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import type { TalentPoolPoolListItem } from "@/lib/types";

function formatGrantedDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function FindMatchesSection() {
  const container = useThemeScopeContainer();
  const { data: jobs, isLoading: jobsLoading } = useMyShadowJobs();
  const [jobId, setJobId] = React.useState<string | undefined>(undefined);
  const { data: results, isLoading: searching } = useTalentPoolMatches(jobId, {
    enabled: !!jobId,
  });

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-foreground">
          Find matches for a role
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Rank your granted Talent Pool candidates against one of your roles.
        </p>
      </div>

      <div className="max-w-sm">
        <Select value={jobId} onValueChange={setJobId} disabled={jobsLoading}>
          <SelectTrigger>
            <SelectValue placeholder="Choose a role…" />
          </SelectTrigger>
          <SelectContent container={container}>
            {jobs?.map((job) => (
              <SelectItem key={job.id} value={job.id}>
                {job.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!jobId && (
        <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-border py-16 text-center">
          <Search className="h-5 w-5 text-muted-foreground" />
          <p className="text-sm font-medium text-foreground">Pick a role to get started</p>
          <p className="max-w-xs text-sm text-muted-foreground">
            We&apos;ll rank your Talent Pool candidates by how well they match it.
          </p>
        </div>
      )}

      {jobId && searching && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {jobId && !searching && results?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
            <p className="text-sm text-muted-foreground">
              No Talent Pool candidates are eligible to match this role yet.
            </p>
          </CardContent>
        </Card>
      )}

      {jobId && !searching && results && results.length > 0 && (
        <div className="flex flex-col gap-3">
          {results.map((result) => (
            <CandidateSearchResultCard
              key={result.callsign}
              result={result}
              contextLine={`Previously considered for ${result.source_role_title} · granted ${formatGrantedDate(result.granted_at)}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

const columnHelper = createColumnHelper<TalentPoolPoolListItem>();

const columns = [
  columnHelper.accessor("callsign", {
    header: "Callsign",
    cell: (info) => <span className="font-medium text-foreground">{info.getValue()}</span>,
  }),
  columnHelper.accessor("headline", {
    header: "Headline",
    cell: (info) => {
      const item = info.row.original;
      return (
        <span className="text-muted-foreground">
          {info.getValue() || "—"}
          {item.seniority ? ` · ${item.seniority}` : ""}
        </span>
      );
    },
  }),
  columnHelper.accessor("source_role_title", {
    header: "Source role",
    cell: (info) => <span className="text-foreground">{info.getValue()}</span>,
  }),
  columnHelper.accessor("scope", {
    header: "Scope",
    cell: (info) => <Badge variant="outline">{TALENT_POOL_SCOPE_LABEL[info.getValue()]}</Badge>,
  }),
  columnHelper.accessor("granted_at", {
    header: "Granted",
    cell: (info) => (
      <span className="text-muted-foreground">
        {new Date(info.getValue()).toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })}
      </span>
    ),
  }),
];

export default function TalentPoolPage() {
  const { hasPermission } = useAuth();
  const canView = hasPermission("talent_pool.view");
  const { data: pool, isLoading } = useCompanyTalentPool();
  const [sorting, setSorting] = React.useState<SortingState>([]);

  const table = useReactTable({
    data: pool ?? [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Talent Pool isn&apos;t available on your role</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Talent Pool</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Candidates who&apos;ve chosen to stay discoverable for future roles at your company.
        </p>
      </div>

      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : pool && pool.length > 0 ? (
        <Card>
          <CardContent className="p-0">
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
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-border py-16 text-center">
          <p className="text-sm font-medium text-foreground">No one in your Talent Pool yet</p>
          <p className="max-w-xs text-sm text-muted-foreground">
            Once a candidate approves a Talent Pool request, they&apos;ll show up here.
          </p>
        </div>
      )}

      <FindMatchesSection />
    </div>
  );
}
