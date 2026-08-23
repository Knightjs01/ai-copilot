"use client";

import * as React from "react";
import { Users } from "lucide-react";

import { AddExistingCandidateDialog } from "@/components/project/add-existing-candidate-dialog";
import { CandidatesRoleList } from "@/components/project/candidates-role-list";
import { CandidatesToolbar } from "@/components/project/candidates-toolbar";
import { Skeleton } from "@/components/ui/skeleton";
import { useCandidates } from "@/lib/queries/candidates";
import { useProjectShadowJob, useShadowJobApplicants } from "@/lib/queries/shadow-jobs";
import type { CandidateSource } from "@/lib/types";

export function CandidatesTabSection({
  projectId,
  projectTitle,
}: {
  projectId: string;
  projectTitle: string;
}) {
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

  const filteredShadowApplicants = React.useMemo(() => {
    if (!shadowApplicants) return [];
    const query = search.trim().toLowerCase();
    if (query.length === 0) return shadowApplicants;
    return shadowApplicants.filter((applicant) => applicant.callsign.toLowerCase().includes(query));
  }, [shadowApplicants, search]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-10 w-full max-w-md" />
        <Skeleton className="h-64 w-full" />
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
          Candidates apply through the Shadow job board, or you can add an existing Talent Pool
          candidate directly.
        </p>
        <div className="mt-2">
          <AddExistingCandidateDialog projectId={projectId} shadowJobId={shadowJob?.id} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <CandidatesToolbar
        projectId={projectId}
        shadowJobId={shadowJob?.id}
        search={search}
        onSearchChange={setSearch}
        sourceFilter={sourceFilter}
        onSourceFilterChange={setSourceFilter}
        matchCount={filteredCandidates.length}
        totalCount={candidates?.length ?? 0}
      />
      <CandidatesRoleList
        projectTitle={projectTitle}
        candidates={filteredCandidates}
        shadowJobId={shadowJob?.id}
        shadowApplicants={filteredShadowApplicants}
      />
    </div>
  );
}
