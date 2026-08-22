"use client";

import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { DndContext, type DragEndEvent, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { MessageCircle, Tag } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { KanbanCard, KanbanColumn } from "@/components/ui/kanban";
import { apiClient } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type {
  Candidate,
  CandidateStatus,
  ShadowEffectiveStage,
  ShadowProfileCompanyWide,
} from "@/lib/types";
import {
  CANDIDATE_SOURCE_LABEL,
  NOTICE_PERIOD_LABEL,
  PRESCREEN_OUTCOME_LABEL,
  PRESCREEN_OUTCOME_VARIANT,
  SHADOW_APPLICATION_STATUS_LABEL,
  SHADOW_APPLICATION_STATUS_VARIANT,
  SHADOW_EFFECTIVE_STAGE_COLUMNS,
  SHADOW_EFFECTIVE_STAGE_LABEL,
} from "@/lib/status-display";

// Same kind-prefixed drag-id convention as MergedPipelineKanban (the per-project version) — this
// sibling exists because a cross-project board needs a per-applicant shadow_job_id for both the
// pipeline-stage mutation and the card's link target, where the per-project version can bind a
// single shadowJobId once for the whole board.
const candidateDragId = (id: string) => `candidate:${id}`;
const shadowDragId = (id: string) => `shadow:${id}`;

export function CrossProjectPipelineKanban({
  candidatesQueryKey,
  candidates,
  shadowApplicantsQueryKey,
  shadowApplicants,
  projectTitles,
}: {
  candidatesQueryKey: unknown[];
  candidates: Candidate[];
  shadowApplicantsQueryKey: unknown[];
  shadowApplicants: ShadowProfileCompanyWide[];
  projectTitles: Record<string, string>;
}) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));

  const handleDragEnd = async (event: DragEndEvent) => {
    const dragId = event.active.id as string;
    const newStage = event.over?.id as ShadowEffectiveStage | undefined;
    if (!newStage) return;

    if (dragId.startsWith("candidate:")) {
      const candidateId = dragId.slice("candidate:".length);
      const current = queryClient.getQueryData<Candidate[]>(candidatesQueryKey);
      const candidate = current?.find((c) => c.id === candidateId);
      if (!candidate || candidate.status === newStage) return;

      queryClient.setQueryData<Candidate[]>(candidatesQueryKey, (prev) =>
        prev?.map((c) =>
          c.id === candidateId ? { ...c, status: newStage as CandidateStatus } : c
        )
      );
      try {
        await apiClient.patch<Candidate>(`/candidates/${candidateId}`, { status: newStage });
      } catch {
        toast({
          title: "Couldn't move candidate",
          description: "The status change didn't save. Try again.",
          variant: "danger",
        });
      } finally {
        void queryClient.invalidateQueries({ queryKey: candidatesQueryKey });
      }
      return;
    }

    const applicationId = dragId.slice("shadow:".length);
    const applicant = shadowApplicants.find((a) => a.application_id === applicationId);
    if (!applicant || applicant.effective_stage === newStage) return;

    if (newStage === "withdrawn") {
      toast({
        title: "Can't move this here",
        description: "Candidates withdraw their own Shadow applications — you can't move them here.",
        variant: "danger",
      });
      return;
    }

    try {
      await apiClient.patch(
        `/shadow-jobs/mine/${applicant.shadow_job_id}/applicants/${applicationId}`,
        { pipeline_stage: newStage }
      );
    } catch {
      toast({
        title: "Couldn't move applicant",
        description: "The stage change didn't save. Try again.",
        variant: "danger",
      });
    } finally {
      void queryClient.invalidateQueries({ queryKey: shadowApplicantsQueryKey });
    }
  };

  const candidatesByStage = (stage: ShadowEffectiveStage) =>
    candidates.filter((c) => c.status === stage);
  const applicantsByStage = (stage: ShadowEffectiveStage) =>
    shadowApplicants.filter((a) => a.effective_stage === stage);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold tracking-tight text-foreground">Pipeline</h2>
      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {SHADOW_EFFECTIVE_STAGE_COLUMNS.map((stage) => {
            const stageCandidates = candidatesByStage(stage);
            const stageApplicants = applicantsByStage(stage);
            return (
              <KanbanColumn
                key={stage}
                id={stage}
                title={SHADOW_EFFECTIVE_STAGE_LABEL[stage]}
                count={stageCandidates.length + stageApplicants.length}
              >
                {stageCandidates.map((candidate) => (
                  <Link
                    key={candidate.id}
                    href={`/projects/${candidate.project_id}/candidates/${candidate.id}`}
                  >
                    <KanbanCard id={candidateDragId(candidate.id)}>
                      <div className="flex items-center gap-2.5">
                        <Avatar name={candidate.callsign} className="h-7 w-7 text-[10px]" />
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-foreground">
                            {candidate.callsign}
                          </p>
                          <p className="truncate text-xs text-muted-foreground">
                            {candidate.candidate_ref}
                          </p>
                          {projectTitles[candidate.project_id] && (
                            <p className="truncate text-xs text-brand">
                              {projectTitles[candidate.project_id]}
                            </p>
                          )}
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

                {stageApplicants.map((applicant) => (
                  <Link key={applicant.application_id} href={`/shadow-jobs/${applicant.shadow_job_id}`}>
                    <KanbanCard
                      id={shadowDragId(applicant.application_id)}
                      className={applicant.is_new ? "border-brand/50 bg-brand/5" : undefined}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="relative shrink-0">
                          <Avatar name={applicant.callsign} className="h-7 w-7 text-[10px]" />
                          {applicant.is_new && (
                            <span
                              className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-card bg-success"
                              aria-hidden
                            />
                          )}
                        </span>
                        <div className="min-w-0">
                          <p className="flex items-center gap-1.5 truncate text-sm font-medium text-foreground">
                            {applicant.callsign}
                            {applicant.is_new && (
                              <Badge variant="success" className="shrink-0 text-[10px]">
                                New application
                              </Badge>
                            )}
                          </p>
                          <p className="truncate text-xs text-brand">{applicant.job_title}</p>
                        </div>
                      </div>

                      {applicant.skills.length > 0 && (
                        <div className="mt-2.5 flex flex-wrap gap-1">
                          {applicant.skills.slice(0, 4).map((skill) => (
                            <Badge key={skill} variant="neutral" className="text-[10px]">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      )}

                      {applicant.unread_message_count > 0 && (
                        <div className="mt-2.5 flex items-center gap-1.5 text-xs font-medium text-info">
                          <MessageCircle className="h-3.5 w-3.5 shrink-0" />
                          {applicant.unread_message_count} new message
                          {applicant.unread_message_count === 1 ? "" : "s"}
                        </div>
                      )}

                      {(applicant.status === "reveal_requested" ||
                        applicant.status === "revealed" ||
                        applicant.status === "declined") && (
                        <Badge
                          variant={SHADOW_APPLICATION_STATUS_VARIANT[applicant.status]}
                          className="mt-2.5"
                        >
                          {SHADOW_APPLICATION_STATUS_LABEL[applicant.status]}
                        </Badge>
                      )}
                    </KanbanCard>
                  </Link>
                ))}
              </KanbanColumn>
            );
          })}
        </div>
      </DndContext>
    </div>
  );
}
