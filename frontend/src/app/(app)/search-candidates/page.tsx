"use client";

import * as React from "react";
import { Search } from "lucide-react";

import { CandidateSearchResultCard } from "@/components/candidate-search/candidate-search-result-card";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { useCandidateSearch } from "@/lib/queries/candidate-search";
import { useMyShadowJobs } from "@/lib/queries/shadow-jobs";

export default function SearchCandidatesPage() {
  const container = useThemeScopeContainer();
  const { data: jobs, isLoading: jobsLoading } = useMyShadowJobs();
  const [jobId, setJobId] = React.useState<string | undefined>(undefined);
  const { data: results, isLoading: searching } = useCandidateSearch(jobId, {
    enabled: !!jobId,
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Search Candidates
        </h1>
        <p className="text-sm text-muted-foreground">
          Pick a role to see discoverable Shadow candidates ranked by AI match.
        </p>
      </div>

      <div className="max-w-sm">
        <Select value={jobId} onValueChange={setJobId} disabled={jobsLoading}>
          <SelectTrigger>
            <SelectValue placeholder="Choose a role…" />
          </SelectTrigger>
          <SelectContent container={container}>
            {jobs?.map((job) => (
              <SelectItem key={job.id} value={job.id}>
                {job.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!jobId && (
        <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-border py-16 text-center">
          <Search className="h-5 w-5 text-muted-foreground" />
          <p className="text-sm font-medium text-foreground">Pick a role to get started</p>
          <p className="max-w-xs text-sm text-muted-foreground">
            We&apos;ll rank discoverable candidates by how well they match it.
          </p>
        </div>
      )}

      {jobId && searching && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {jobId && !searching && results?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
            <p className="text-sm text-muted-foreground">
              No discoverable candidates match this role yet.
            </p>
          </CardContent>
        </Card>
      )}

      {jobId && !searching && results && results.length > 0 && (
        <div className="flex flex-col gap-3">
          {results.map((result) => (
            <CandidateSearchResultCard key={result.callsign} result={result} />
          ))}
        </div>
      )}
    </div>
  );
}
