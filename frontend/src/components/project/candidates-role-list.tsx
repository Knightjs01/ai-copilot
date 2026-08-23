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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useUpdateCandidate } from "@/lib/queries/candidates";
import { useUpdateApplicantPipelineStage } from "@/lib/queries/shadow-jobs";
import { CANDIDATE_STATUS_COLUMNS, CANDIDATE_STATUS_LABEL, SHADOW_EFFECTIVE_STAGE_LABEL } from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { useToast } from "@/lib/toast-context";
import type { Candidate, CandidateStatus, ShadowPipelineStage, ShadowProfile } from "@/lib/types";

const SHADOW_ASSIGNABLE_STAGES = ["new", "screening", "interviewing", "offer", "hired", "rejected"] as const;

type MergedRow =
  | { kind: "candidate"; key: string; candidate: Candidate }
  | { kind: "shadow"; key: string; applicant: ShadowProfile };

function CandidateStageSelect({ candidate }: { candidate: Candidate }) {
  const updateCandidate = useUpdateCandidate(candidate.id, candidate.project_id);
  const container = useThemeScopeContainer();
  const toast = useToast();

  const handleChange = (value: CandidateStatus) => {
    updateCandidate.mutate(
      { status: value },
      {
        onError: () =>
          toast({ title: "Couldn't update stage", description: "Try again.", variant: "danger" }),
      }
    );
  };

  return (
    <Select value={candidate.status} onValueChange={(value) => handleChange(value as CandidateStatus)}>
      <SelectTrigger className="h-8 w-36 text-xs">
        <SelectValue />
      </SelectTrigger>
      <SelectContent container={container}>
        {CANDIDATE_STATUS_COLUMNS.map((status) => (
          <SelectItem key={status} value={status}>
            {CANDIDATE_STATUS_LABEL[status]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function ShadowStageSelect({ shadowJobId, applicant }: { shadowJobId: string; applicant: ShadowProfile }) {
  const updatePipelineStage = useUpdateApplicantPipelineStage(shadowJobId);
  const container = useThemeScopeContainer();
  const toast = useToast();

  // Withdrawal is candidate-only and derived, never recruiter-set -- mirrors the merged Kanban's
  // own drop-rejection rule (see merged-pipeline-kanban.tsx). Once withdrawn, the stage is fixed.
  if (applicant.effective_stage === "withdrawn") {
    return <Badge variant="neutral">{SHADOW_EFFECTIVE_STAGE_LABEL.withdrawn}</Badge>;
  }

  const handleChange = (value: ShadowPipelineStage) => {
    updatePipelineStage.mutate(
      { applicationId: applicant.application_id, pipelineStage: value },
      {
        onError: () =>
          toast({ title: "Couldn't update stage", description: "Try again.", variant: "danger" }),
      }
    );
  };

  return (
    <Select
      value={applicant.pipeline_stage}
      onValueChange={(value) => handleChange(value as ShadowPipelineStage)}
    >
      <SelectTrigger className="h-8 w-36 text-xs">
        <SelectValue />
      </SelectTrigger>
      <SelectContent container={container}>
        {SHADOW_ASSIGNABLE_STAGES.map((stage) => (
          <SelectItem key={stage} value={stage}>
            {SHADOW_EFFECTIVE_STAGE_LABEL[stage]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

const columnHelper = createColumnHelper<MergedRow>();

const columns = [
  columnHelper.accessor(
    (row) => (row.kind === "candidate" ? row.candidate.callsign : row.applicant.callsign),
    {
      id: "callsign",
      header: "Callsign",
      cell: (info) => {
        const row = info.row.original;
        const href =
          row.kind === "candidate"
            ? `/projects/${row.candidate.project_id}/candidates/${row.candidate.id}`
            : `/shadow-jobs/${info.table.options.meta?.shadowJobId}`;
        return (
          <Link href={href} className="font-medium text-foreground hover:underline">
            {info.getValue()}
          </Link>
        );
      },
    }
  ),
  columnHelper.display({
    id: "title",
    header: "Title",
    cell: (info) => (
      <span className="text-muted-foreground">{info.table.options.meta?.projectTitle}</span>
    ),
  }),
  columnHelper.display({
    id: "role_stage",
    header: "Role Stage",
    cell: (info) => {
      const row = info.row.original;
      return row.kind === "candidate" ? (
        <CandidateStageSelect candidate={row.candidate} />
      ) : (
        <ShadowStageSelect
          shadowJobId={info.table.options.meta?.shadowJobId ?? ""}
          applicant={row.applicant}
        />
      );
    },
  }),
  columnHelper.display({
    id: "revealed",
    header: "Revealed",
    cell: (info) => {
      const row = info.row.original;
      const revealed = row.kind === "candidate" ? row.candidate.is_revealed : row.applicant.status === "revealed";
      return (
        <Badge variant={revealed ? "success" : "neutral"}>{revealed ? "Yes" : "No"}</Badge>
      );
    },
  }),
];

declare module "@tanstack/react-table" {
  interface TableMeta<TData> {
    projectTitle?: string;
    shadowJobId?: string;
  }
}

export function CandidatesRoleList({
  projectTitle,
  candidates,
  shadowJobId,
  shadowApplicants,
}: {
  projectTitle: string;
  candidates: Candidate[];
  shadowJobId?: string;
  shadowApplicants: ShadowProfile[];
}) {
  const [sorting, setSorting] = React.useState<SortingState>([]);

  const rows = React.useMemo<MergedRow[]>(
    () => [
      ...candidates.map((candidate): MergedRow => ({ kind: "candidate", key: candidate.id, candidate })),
      ...shadowApplicants.map(
        (applicant): MergedRow => ({ kind: "shadow", key: applicant.application_id, applicant })
      ),
    ],
    [candidates, shadowApplicants]
  );

  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getRowId: (row) => row.key,
    meta: { projectTitle, shadowJobId },
  });

  if (rows.length === 0) {
    return null;
  }

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
