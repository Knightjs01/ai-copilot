"use client";

import * as React from "react";
import Link from "next/link";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  CANDIDATE_SOURCE_LABEL,
  CANDIDATE_STATUS_LABEL,
  CANDIDATE_STATUS_VARIANT,
  PRESCREEN_OUTCOME_LABEL,
  PRESCREEN_OUTCOME_VARIANT,
} from "@/lib/status-display";
import type { Candidate } from "@/lib/types";

const columnHelper = createColumnHelper<Candidate>();

const columns = [
  columnHelper.accessor("callsign", {
    header: "Callsign",
    cell: (info) => (
      <Link
        href={`/projects/${info.row.original.project_id}/candidates/${info.row.original.id}`}
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
  columnHelper.accessor("source", {
    header: "Source",
    cell: (info) => {
      const candidate = info.row.original;
      return (
        <span className="text-foreground">
          {CANDIDATE_SOURCE_LABEL[candidate.source]}
          {candidate.source === "agency" && candidate.agency_name
            ? ` (${candidate.agency_name})`
            : ""}
        </span>
      );
    },
  }),
  columnHelper.accessor("prescreen_outcome", {
    header: "Pre-screen outcome",
    sortingFn: "text",
    cell: (info) => {
      const outcome = info.getValue();
      return outcome ? (
        <Badge variant={PRESCREEN_OUTCOME_VARIANT[outcome]}>{PRESCREEN_OUTCOME_LABEL[outcome]}</Badge>
      ) : (
        <span className="text-muted-foreground">—</span>
      );
    },
  }),
  columnHelper.accessor("expected_salary", {
    header: "Expected salary",
    cell: (info) => {
      const salary = info.getValue();
      return (
        <span className="text-foreground">
          {salary != null ? `£${salary.toLocaleString()}` : "—"}
        </span>
      );
    },
  }),
];

export function CandidatesListTab({ candidates }: { candidates: Candidate[] }) {
  const [sorting, setSorting] = React.useState<SortingState>([]);

  const table = useReactTable({
    data: candidates,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  if (candidates.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold tracking-tight text-foreground">All candidates</h2>
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
    </div>
  );
}
