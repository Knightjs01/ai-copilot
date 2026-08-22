"use client";

import * as React from "react";
import { ShieldAlert, Users } from "lucide-react";

import { CandidatesKanban } from "@/components/project/candidates-kanban";
import { CandidatesListTab } from "@/components/project/candidates-list-tab";
import { CandidatesToolbar } from "@/components/project/candidates-toolbar";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth-context";
import { useAllCandidates } from "@/lib/queries/candidates";
import { useProjects } from "@/lib/queries/projects";
import { cn } from "@/lib/utils";
import type { CandidateSource } from "@/lib/types";

type OwnerFilter = "all" | "mine";

export default function PipelinePage() {
  const { hasPermission, user } = useAuth();
  const canView = hasPermission("candidates.view");
  const { data: candidates, isLoading: candidatesLoading } = useAllCandidates();
  const { data: projects, isLoading: projectsLoading } = useProjects();
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

  const isLoading = candidatesLoading || projectsLoading;

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

  if (!candidates || candidates.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <Users className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">No candidates yet</p>
        <p className="max-w-xs text-sm text-muted-foreground">
          Candidates across every role you can see will appear here once you add them from a role.
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
        matchCount={filteredCandidates.length}
        totalCount={candidates.length}
      />
      <CandidatesKanban
        queryKey={["candidates", "all"]}
        candidates={filteredCandidates}
        projectTitles={projectTitles}
      />
      <CandidatesListTab candidates={filteredCandidates} />
    </div>
  );
}
