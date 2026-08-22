"use client";

import * as React from "react";
import Link from "next/link";
import { Briefcase } from "lucide-react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";

import { NewProjectDialog } from "@/components/new-project-dialog";
import { DashboardPanel } from "@/components/project/dashboard-panel";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useProjects } from "@/lib/queries/projects";
import { PROJECT_STATUS_LABEL, PROJECT_STATUS_VARIANT } from "@/lib/status-display";
import { cn } from "@/lib/utils";
import type { Project, ProjectStatus } from "@/lib/types";

// The real ProjectStatus enum -- no "Archived" chip, that status doesn't exist.
const STATUS_FILTERS: { value: ProjectStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "open", label: "Open" },
  { value: "draft", label: "Draft" },
  { value: "on_hold", label: "Paused" },
  { value: "filled", label: "Filled" },
  { value: "cancelled", label: "Cancelled" },
];

function formatSalary(min: number | null, max: number | null): string | null {
  if (!min && !max) return null;
  const fmt = (n: number) => `£${(n / 1000).toFixed(0)}k`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  return fmt((min ?? max)!);
}

const columnHelper = createColumnHelper<Project>();

const columns = [
  columnHelper.accessor("title", {
    header: "Role",
    cell: (info) => (
      <Link
        href={`/projects/${info.row.original.id}`}
        className="font-medium text-foreground hover:underline"
      >
        {info.getValue()}
      </Link>
    ),
  }),
  columnHelper.accessor("department", {
    header: "Department",
    cell: (info) => <span className="text-foreground">{info.getValue() || "—"}</span>,
  }),
  columnHelper.accessor("seniority", {
    header: "Seniority",
    cell: (info) => <span className="text-foreground">{info.getValue() || "—"}</span>,
  }),
  columnHelper.accessor("location", {
    header: "Location",
    cell: (info) => <span className="text-foreground">{info.getValue() || "—"}</span>,
  }),
  columnHelper.accessor((row) => row.salary_min, {
    id: "salary",
    header: "Salary",
    cell: (info) => (
      <span className="text-foreground">
        {formatSalary(info.row.original.salary_min, info.row.original.salary_max) || "—"}
      </span>
    ),
  }),
  columnHelper.accessor("status", {
    header: "Status",
    cell: (info) => (
      <Badge variant={PROJECT_STATUS_VARIANT[info.getValue()]}>
        {PROJECT_STATUS_LABEL[info.getValue()]}
      </Badge>
    ),
  }),
];

function ProjectsTable({ projects }: { projects: Project[] }) {
  const [sorting, setSorting] = React.useState<SortingState>([]);

  const table = useReactTable({
    data: projects,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
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
  );
}

export default function ProjectsPage() {
  const { data: projects, isLoading } = useProjects();
  const [statusFilter, setStatusFilter] = React.useState<ProjectStatus | "all">("all");

  const filtered =
    statusFilter === "all" ? projects ?? [] : (projects ?? []).filter((p) => p.status === statusFilter);

  return (
    <div className="grid grid-cols-1 gap-8 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="flex flex-col gap-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              Hiring projects
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Manage pre-screen for every open role.
            </p>
          </div>
          <NewProjectDialog />
        </div>

        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setStatusFilter(f.value)}
              className={cn(
                "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
                statusFilter === f.value
                  ? "bg-brand/10 text-brand"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="flex justify-center py-24">
            <Spinner className="h-6 w-6 text-muted-foreground" />
          </div>
        ) : filtered.length > 0 ? (
          <ProjectsTable projects={filtered} />
        ) : (
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
            <Briefcase className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm font-medium text-foreground">No hiring projects yet</p>
            <p className="max-w-xs text-sm text-muted-foreground">
              Create your first project to start screening candidates.
            </p>
          </div>
        )}
      </div>

      <DashboardPanel />
    </div>
  );
}
