"use client";

import * as React from "react";
import Link from "next/link";
import { DndContext, type DragEndEvent, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";

import { AddCandidateDialog } from "@/components/project/add-candidate-dialog";
import { Badge } from "@/components/ui/badge";
import { KanbanCard, KanbanColumn } from "@/components/ui/kanban";
import { Spinner } from "@/components/ui/spinner";
import { apiClient } from "@/lib/api-client";
import { useQueryClient } from "@tanstack/react-query";
import { useCandidates } from "@/lib/queries/candidates";
import type { Candidate, CandidateStatus } from "@/lib/types";
import {
  CANDIDATE_STATUS_COLUMNS,
  CANDIDATE_STATUS_LABEL,
  PRESCREEN_OUTCOME_LABEL,
  PRESCREEN_OUTCOME_VARIANT,
} from "@/lib/status-display";

export function CandidatesKanban({ projectId }: { projectId: string }) {
  const { data: candidates, isLoading } = useCandidates(projectId);
  const queryClient = useQueryClient();
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));

  const handleDragEnd = async (event: DragEndEvent) => {
    const candidateId = event.active.id as string;
    const newStatus = event.over?.id as CandidateStatus | undefined;
    if (!newStatus) return;

    const current = queryClient.getQueryData<Candidate[]>(["candidates", { projectId }]);
    const candidate = current?.find((c) => c.id === candidateId);
    if (!candidate || candidate.status === newStatus) return;

    // Optimistic move so the drag feels instant, then reconcile with the server.
    queryClient.setQueryData<Candidate[]>(["candidates", { projectId }], (prev) =>
      prev?.map((c) => (c.id === candidateId ? { ...c, status: newStatus } : c))
    );
    try {
      await apiClient.patch<Candidate>(`/candidates/${candidateId}`, { status: newStatus });
    } finally {
      void queryClient.invalidateQueries({ queryKey: ["candidates", { projectId }] });
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  const byStatus = (status: CandidateStatus) =>
    (candidates ?? []).filter((c) => c.status === status);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold tracking-tight text-foreground">Candidates</h2>
        <AddCandidateDialog projectId={projectId} />
      </div>
      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {CANDIDATE_STATUS_COLUMNS.map((status) => (
            <KanbanColumn
              key={status}
              id={status}
              title={CANDIDATE_STATUS_LABEL[status]}
              count={byStatus(status).length}
            >
              {byStatus(status).map((candidate) => (
                <Link key={candidate.id} href={`/projects/${projectId}/candidates/${candidate.id}`}>
                  <KanbanCard id={candidate.id}>
                    <p className="text-sm font-medium text-foreground">{candidate.full_name}</p>
                    {candidate.email && (
                      <p className="mt-0.5 truncate text-xs text-muted-foreground">
                        {candidate.email}
                      </p>
                    )}
                    {candidate.prescreen_outcome && (
                      <Badge
                        variant={PRESCREEN_OUTCOME_VARIANT[candidate.prescreen_outcome]}
                        className="mt-2"
                      >
                        {PRESCREEN_OUTCOME_LABEL[candidate.prescreen_outcome]}
                      </Badge>
                    )}
                  </KanbanCard>
                </Link>
              ))}
            </KanbanColumn>
          ))}
        </div>
      </DndContext>
    </div>
  );
}
