"use client";

import * as React from "react";
import { ShieldAlert, Users } from "lucide-react";

import { CandidatesListTab } from "@/components/project/candidates-list-tab";
import { CandidatesToolbar } from "@/components/project/candidates-toolbar";
import { CrossProjectPipelineKanban } from "@/components/project/cross-project-pipeline-kanban";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth-context";
import { useAllCandidates } from "@/lib/queries/candidates";
import { useProjects } from "@/lib/queries/projects";
import { useAllShadowApplicants } from "@/lib/queries/shadow-jobs";
import { cn } from "@/lib/utils";
import type { CandidateSource } from "@/lib/types";

type OwnerFilter = "all" | "mine";

const SHADOW_APPLICANTS_QUERY_KEY = ["shadow-jobs", "applicants", "mine-company"];

export default function PipelinePage() {
  const { hasPermission, user } = useAuth();
  const canView = hasPermission("candidates.view");
  const { data: candidates, isLoading: candidatesLoading } = useAllCandidates();
  const { data: projects, isLoading: projectsLoading } = useProjects();
  const { data: shadowApplicants, isLoading: shadowApplicantsLoading } = useAllShadowApplicants({
    enabled: canView,
  });
  const [search, setSearch] = React.useState("");
  const [sourceFilter, setSourceFilter] = React.useState<CandidateSource | "all">("all");
  const [ownerFilter, setOwnerFilter] = React.useState<OwnerFilter>("all");

  const projectTitles = React.useMemo(() => {
    const map: Record<string, string> = {};
    for (const project of projects ?? []) {
      map[project.id] = project.title;
    }
    return map;
  }, [projects]);

  const filteredCandidates = React.useMemo(() => {
    if (!candidates) return [];
    const query = search.trim().toLowerCase();
    return candidates.filter((candidate) => {
      const matchesSearch =
        query.length === 0 ||
        candidate.callsign.toLowerCase().includes(query) ||
        candidate.candidate_ref.toLowerCase().includes(query);
      const matchesSource = sourceFilter === "all" || candidate.source === sourceFilter;
      const matchesOwner = ownerFilter === "all" || candidate.created_by_id === user?.id;
      return matchesSearch && matchesSource && matchesOwner;
    });
  }, [candidates, search, sourceFilter, ownerFilter, user?.id]);

  // Shadow applicants have no "created by a specific recruiter" concept (they applied
  // themselves) and no `source` field -- the owner/source filters only meaningfully apply to
  // directly-added ATS candidates, so applicants are shown under "All Candidates" only, filtered
  // just by callsign search.
  const filteredShadowApplicants = React.useMemo(() => {
    if (!shadowApplicants || ownerFilter === "mine") return [];
    const query = search.trim().toLowerCase();
    return shadowApplicants.filter(
      (applicant) => query.length === 0 || applicant.callsign.toLowerCase().includes(query)
    );
  }, [shadowApplicants, search, ownerFilter]);

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Pipeline is Admin-only</p>
        <p className="max-w-xs text-sm text-muted-foreground">
          Ask an Owner or Admin on your team for access.
        </p>
      </div>
    );
  }

  const isLoading = candidatesLoading || projectsLoading || shadowApplicantsLoading;

  if (isLoading) {
    return (
      <div className="flex flex-col gap-8">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-10 w-full max-w-md" />
        <div className="flex gap-4 overflow-x-auto pb-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-64 w-72 shrink-0" />
          ))}
        </div>
      </div>
    );
  }

  const hasAnyCandidates =
    (candidates && candidates.length > 0) || (shadowApplicants && shadowApplicants.length > 0);

  if (!hasAnyCandidates) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <Users className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">No candidates yet</p>
        <p className="max-w-xs text-sm text-muted-foreground">
          Everyone who applies through the Shadow job board, or is added from a role&apos;s
          Talent Pool, will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Pipeline</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Every candidate across every role, in one board.
        </p>
      </div>

      <div className="flex gap-2">
        {(["all", "mine"] as const).map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => setOwnerFilter(value)}
            className={cn(
              "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
              ownerFilter === value
                ? "bg-brand/10 text-brand"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground"
            )}
          >
            {value === "all" ? "All Candidates" : "My Candidates"}
          </button>
        ))}
      </div>

      <CandidatesToolbar
        search={search}
        onSearchChange={setSearch}
        sourceFilter={sourceFilter}
        onSourceFilterChange={setSourceFilter}
        matchCount={filteredCandidates.length + filteredShadowApplicants.length}
        totalCount={(candidates?.length ?? 0) + (shadowApplicants?.length ?? 0)}
      />
      <CrossProjectPipelineKanban
        candidatesQueryKey={["candidates", "all"]}
        candidates={filteredCandidates}
        shadowApplicantsQueryKey={SHADOW_APPLICANTS_QUERY_KEY}
        shadowApplicants={filteredShadowApplicants}
        projectTitles={projectTitles}
      />
      <CandidatesListTab candidates={filteredCandidates} />
    </div>
  );
}
