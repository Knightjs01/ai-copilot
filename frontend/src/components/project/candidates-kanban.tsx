"use client";

import Link from "next/link";
import { DndContext, type DragEndEvent, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { Tag } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { KanbanCard, KanbanColumn } from "@/components/ui/kanban";
import { apiClient } from "@/lib/api-client";
import { useQueryClient } from "@tanstack/react-query";
import type { Candidate, CandidateStatus } from "@/lib/types";
import {
  CANDIDATE_SOURCE_LABEL,
  CANDIDATE_STATUS_COLUMNS,
  CANDIDATE_STATUS_LABEL,
  NOTICE_PERIOD_LABEL,
  PRESCREEN_OUTCOME_LABEL,
  PRESCREEN_OUTCOME_VARIANT,
} from "@/lib/status-display";

export function CandidatesKanban({
  projectId,
  candidates,
}: {
  projectId: string;
  candidates: Candidate[];
}) {
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

  const byStatus = (status: CandidateStatus) => candidates.filter((c) => c.status === status);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold tracking-tight text-foreground">Pipeline</h2>
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
                    <div className="flex items-center gap-2.5">
                      <Avatar name={candidate.callsign} className="h-7 w-7 text-[10px]" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-foreground">
                          {candidate.callsign}
                        </p>
                        <p className="truncate text-xs text-muted-foreground">
                          {candidate.candidate_ref}
                        </p>
                      </div>
                    </div>

                    <div className="mt-2.5 flex flex-col gap-1 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1.5">
                        <Tag className="h-3 w-3 shrink-0" />
                        {CANDIDATE_SOURCE_LABEL[candidate.source]}
                        {candidate.source === "agency" && candidate.agency_name
                          ? ` · ${candidate.agency_name}`
                          : ""}
                      </span>
                      {candidate.expected_salary != null && (
                        <span>£{candidate.expected_salary.toLocaleString()}</span>
                      )}
                      {candidate.notice_period && (
                        <span>{NOTICE_PERIOD_LABEL[candidate.notice_period]} notice</span>
                      )}
                    </div>

                    {candidate.prescreen_outcome && (
                      <Badge
                        variant={PRESCREEN_OUTCOME_VARIANT[candidate.prescreen_outcome]}
                        className="mt-2.5"
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
