"use client";

import * as React from "react";
import { Search } from "lucide-react";

import { BulkSaveToTalentPoolDialog } from "@/components/candidate-search/bulk-save-to-talent-pool-dialog";
import { CandidateSearchResultCard } from "@/components/candidate-search/candidate-search-result-card";
import { Button } from "@/components/ui/button";
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
  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const [bulkDialogOpen, setBulkDialogOpen] = React.useState(false);

  React.useEffect(() => {
    setSelected(new Set());
  }, [jobId]);

  const toggleSelected = (callsign: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(callsign)) next.delete(callsign);
      else next.add(callsign);
      return next;
    });
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Phantom Smart Talent
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
          {selected.size > 0 && (
            <div className="sticky top-16 z-10 flex items-center justify-between gap-3 rounded-xl border border-brand/30 bg-brand/5 px-4 py-2.5">
              <p className="text-sm font-medium text-foreground">
                {selected.size} candidate{selected.size === 1 ? "" : "s"} selected
              </p>
              <div className="flex items-center gap-2">
                <Button variant="secondary" size="sm" onClick={() => setSelected(new Set())}>
                  Clear
                </Button>
                <Button variant="brand" size="sm" onClick={() => setBulkDialogOpen(true)}>
                  Save to Talent Pool
                </Button>
              </div>
            </div>
          )}
          {results.map((result) => (
            <CandidateSearchResultCard
              key={result.callsign}
              result={result}
              selected={selected.has(result.callsign)}
              onToggleSelected={() => toggleSelected(result.callsign)}
            />
          ))}
        </div>
      )}

      {jobId && (
        <BulkSaveToTalentPoolDialog
          open={bulkDialogOpen}
          onOpenChange={setBulkDialogOpen}
          jobId={jobId}
          callsigns={Array.from(selected)}
          onDone={() => setSelected(new Set())}
        />
      )}
    </div>
  );
}
