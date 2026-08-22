"use client";

import * as React from "react";
import { Users } from "lucide-react";

import { AddCandidateDialog } from "@/components/project/add-candidate-dialog";
import { CandidatesKanban } from "@/components/project/candidates-kanban";
import { CandidatesListTab } from "@/components/project/candidates-list-tab";
import { CandidatesToolbar } from "@/components/project/candidates-toolbar";
import { MergedPipelineKanban } from "@/components/project/merged-pipeline-kanban";
import { Skeleton } from "@/components/ui/skeleton";
import { useCandidates } from "@/lib/queries/candidates";
import { useProjectShadowJob, useShadowJobApplicants } from "@/lib/queries/shadow-jobs";
import type { CandidateSource } from "@/lib/types";

export function CandidatesTabSection({ projectId }: { projectId: string }) {
  const { data: candidates, isLoading } = useCandidates(projectId);
  const { data: shadowJob } = useProjectShadowJob(projectId);
  const { data: shadowApplicants } = useShadowJobApplicants(shadowJob?.id);
  const [search, setSearch] = React.useState("");
  const [sourceFilter, setSourceFilter] = React.useState<CandidateSource | "all">("all");

  const filteredCandidates = React.useMemo(() => {
    if (!candidates) return [];
    const query = search.trim().toLowerCase();
    return candidates.filter((candidate) => {
      const matchesSearch =
        query.length === 0 ||
        candidate.callsign.toLowerCase().includes(query) ||
        candidate.candidate_ref.toLowerCase().includes(query);
      const matchesSource = sourceFilter === "all" || candidate.source === sourceFilter;
      return matchesSearch && matchesSource;
    });
  }, [candidates, search, sourceFilter]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-10 w-full max-w-md" />
        <div className="flex gap-4 overflow-x-auto pb-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-64 w-72 shrink-0" />
          ))}
        </div>
      </div>
    );
  }

  const hasShadowApplicants = !!shadowApplicants && shadowApplicants.length > 0;

  if ((!candidates || candidates.length === 0) && !hasShadowApplicants) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <Users className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">No candidates yet</p>
        <p className="max-w-xs text-sm text-muted-foreground">
          Add your first candidate to start screening for this role.
        </p>
        <div className="mt-2">
          <AddCandidateDialog projectId={projectId} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <CandidatesToolbar
        projectId={projectId}
        search={search}
        onSearchChange={setSearch}
        sourceFilter={sourceFilter}
        onSourceFilterChange={setSourceFilter}
        matchCount={filteredCandidates.length}
        totalCount={candidates?.length ?? 0}
      />
      {shadowJob ? (
        <MergedPipelineKanban
          candidatesQueryKey={["candidates", { projectId }]}
          candidates={filteredCandidates}
          shadowJobId={shadowJob.id}
          shadowApplicants={shadowApplicants ?? []}
        />
      ) : (
        <CandidatesKanban
          queryKey={["candidates", { projectId }]}
          candidates={filteredCandidates}
        />
      )}
      <CandidatesListTab candidates={filteredCandidates} />
    </div>
  );
}
