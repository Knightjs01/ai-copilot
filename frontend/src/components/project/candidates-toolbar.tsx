"use client";

import { Search } from "lucide-react";

import { AddCandidateDialog } from "@/components/project/add-candidate-dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { CANDIDATE_SOURCE_LABEL } from "@/lib/status-display";
import type { CandidateSource } from "@/lib/types";

const SOURCE_OPTIONS = Object.keys(CANDIDATE_SOURCE_LABEL) as CandidateSource[];

export function CandidatesToolbar({
  projectId,
  search,
  onSearchChange,
  sourceFilter,
  onSourceFilterChange,
  matchCount,
  totalCount,
}: {
  projectId?: string;
  search: string;
  onSearchChange: (value: string) => void;
  sourceFilter: CandidateSource | "all";
  onSourceFilterChange: (value: CandidateSource | "all") => void;
  matchCount: number;
  totalCount: number;
}) {
  const container = useThemeScopeContainer();

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center">
        <div className="relative w-full sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search callsign or candidate ID…"
            className="pl-9"
          />
        </div>

        <Select
          value={sourceFilter}
          onValueChange={(value) => onSourceFilterChange(value as CandidateSource | "all")}
        >
          <SelectTrigger className="w-full sm:w-44">
            <SelectValue placeholder="All sources" />
          </SelectTrigger>
          <SelectContent container={container}>
            <SelectItem value="all">All sources</SelectItem>
            {SOURCE_OPTIONS.map((source) => (
              <SelectItem key={source} value={source}>
                {CANDIDATE_SOURCE_LABEL[source]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <span className="text-xs text-muted-foreground">
          {matchCount} of {totalCount}
        </span>
      </div>

      {projectId && <AddCandidateDialog projectId={projectId} />}
    </div>
  );
}
