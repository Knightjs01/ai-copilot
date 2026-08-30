"use client";

import * as React from "react";
import { Check, Pencil, Search, ShieldAlert, X } from "lucide-react";
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
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/lib/auth-context";
import { useTalentPoolMatches } from "@/lib/queries/candidate-search";
import { useMyShadowJobs } from "@/lib/queries/shadow-jobs";
import {
  useAssignTalentPool,
  useCompanyTalentPool,
  useRenameTalentPool,
} from "@/lib/queries/talent-pool";
import { TALENT_POOL_SCOPE_LABEL } from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import type { TalentPoolPoolListItem } from "@/lib/types";

const UNGROUPED_LABEL = "Ungrouped";

function formatGrantedDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

// Mirrors saved-jobs/page.tsx's groupByCollection helper exactly -- a pool is just "rows sharing
// this string" (see backend TalentPoolGrant.pool_name's docstring), so grouping stays a pure
// frontend concern over an otherwise-flat list.
function groupByPool(
  items: TalentPoolPoolListItem[]
): Map<string, TalentPoolPoolListItem[]> {
  const groups = new Map<string, TalentPoolPoolListItem[]>();
  for (const item of items) {
    const key = item.pool_name ?? UNGROUPED_LABEL;
    const existing = groups.get(key);
    if (existing) existing.push(item);
    else groups.set(key, [item]);
  }
  return groups;
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

function PoolGroup({
  poolName,
  items,
  columns,
  sorting,
  onSortingChange,
  selectedIds,
  existingPoolNames,
}: {
  poolName: string;
  items: TalentPoolPoolListItem[];
  columns: ReturnType<typeof buildColumns>;
  sorting: SortingState;
  onSortingChange: (sorting: SortingState) => void;
  selectedIds: Set<string>;
  existingPoolNames: string[];
}) {
  const table = useReactTable({
    data: items,
    columns,
    state: { sorting },
    onSortingChange: (updater) =>
      onSortingChange(typeof updater === "function" ? updater(sorting) : updater),
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const [renaming, setRenaming] = React.useState(false);
  const [renameValue, setRenameValue] = React.useState(poolName);
  const renamePool = useRenameTalentPool();

  const handleRename = async () => {
    const trimmed = renameValue.trim();
    if (!trimmed || trimmed === poolName) {
      setRenaming(false);
      return;
    }
    if (existingPoolNames.includes(trimmed)) return;
    await renamePool.mutateAsync({ oldName: poolName, newName: trimmed });
    setRenaming(false);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        {renaming && poolName !== UNGROUPED_LABEL ? (
          <div className="flex items-center gap-1.5">
            <Input
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              className="h-8 max-w-[220px]"
              autoFocus
            />
            <button
              type="button"
              onClick={() => void handleRename()}
              className="text-success"
              aria-label="Save pool name"
            >
              <Check className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => {
                setRenameValue(poolName);
                setRenaming(false);
              }}
              className="text-muted-foreground"
              aria-label="Cancel rename"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <>
            <h3 className="text-sm font-semibold text-foreground">{poolName}</h3>
            <span className="text-xs text-muted-foreground">({items.length})</span>
            {poolName !== UNGROUPED_LABEL && (
              <button
                type="button"
                onClick={() => setRenaming(true)}
                className="text-muted-foreground transition-colors hover:text-foreground"
                aria-label={`Rename ${poolName}`}
              >
                <Pencil className="h-3.5 w-3.5" />
              </button>
            )}
          </>
        )}
      </div>

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
                <TableRow
                  key={row.id}
                  className={selectedIds.has(row.original.id) ? "bg-brand/5" : undefined}
                >
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
    </div>
  );
}

function buildColumns(
  selectedIds: Set<string>,
  onToggle: (id: string) => void
) {
  const columnHelper = createColumnHelper<TalentPoolPoolListItem>();
  return [
    columnHelper.display({
      id: "select",
      header: "",
      cell: (info) => (
        <input
          type="checkbox"
          checked={selectedIds.has(info.row.original.id)}
          onChange={() => onToggle(info.row.original.id)}
          className="h-4 w-4 accent-brand"
          aria-label={`Select ${info.row.original.callsign}`}
        />
      ),
    }),
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
}

export default function TalentPoolPage() {
  const { hasPermission } = useAuth();
  const canView = hasPermission("talent_pool.view");
  const { data: pool, isLoading } = useCompanyTalentPool();
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [selectedIds, setSelectedIds] = React.useState<Set<string>>(new Set());
  const [newPoolName, setNewPoolName] = React.useState("");
  const assignPool = useAssignTalentPool();

  const toggleSelected = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const columns = React.useMemo(() => buildColumns(selectedIds, toggleSelected), [selectedIds]);

  const groups = React.useMemo(() => groupByPool(pool ?? []), [pool]);
  const existingPoolNames = React.useMemo(
    () => [...groups.keys()].filter((name) => name !== UNGROUPED_LABEL),
    [groups]
  );

  const handleAssign = async (poolName: string) => {
    if (!poolName.trim() || selectedIds.size === 0) return;
    await assignPool.mutateAsync({ grantIds: Array.from(selectedIds), poolName: poolName.trim() });
    setSelectedIds(new Set());
    setNewPoolName("");
  };

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
        <div className="flex flex-col gap-6">
          {selectedIds.size > 0 && (
            <div className="sticky top-16 z-10 flex flex-wrap items-center gap-2 rounded-xl border border-brand/30 bg-brand/5 px-4 py-2.5">
              <p className="text-sm font-medium text-foreground">
                {selectedIds.size} selected
              </p>
              <Button variant="secondary" size="sm" onClick={() => setSelectedIds(new Set())}>
                Clear
              </Button>
              <div className="flex flex-wrap items-center gap-1.5">
                {existingPoolNames.map((name) => (
                  <button
                    key={name}
                    type="button"
                    onClick={() => void handleAssign(name)}
                    className="rounded-full border border-border bg-card px-2.5 py-1 text-xs font-medium text-foreground transition-colors hover:border-brand hover:text-brand"
                  >
                    Add to {name}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1.5">
                <Input
                  value={newPoolName}
                  onChange={(e) => setNewPoolName(e.target.value)}
                  placeholder="New pool name"
                  className="h-8 w-40"
                />
                <Button
                  variant="brand"
                  size="sm"
                  disabled={!newPoolName.trim()}
                  onClick={() => void handleAssign(newPoolName)}
                >
                  Add
                </Button>
              </div>
            </div>
          )}

          {[...groups.entries()].map(([poolName, items]) => (
            <PoolGroup
              key={poolName}
              poolName={poolName}
              items={items}
              columns={columns}
              sorting={sorting}
              onSortingChange={setSorting}
              selectedIds={selectedIds}
              existingPoolNames={existingPoolNames}
            />
          ))}
        </div>
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
