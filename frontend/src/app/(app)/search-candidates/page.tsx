"use client";

import * as React from "react";
import { Columns3, Search, Zap } from "lucide-react";

import { BulkSaveToTalentPoolDialog } from "@/components/candidate-search/bulk-save-to-talent-pool-dialog";
import {
  CandidateSearchResultCard,
  type QuickTalentPoolState,
} from "@/components/candidate-search/candidate-search-result-card";
import { CandidateCompareDialog } from "@/components/candidate-search/candidate-compare-dialog";
import { CandidateQuickViewDialog } from "@/components/candidate-search/candidate-quick-view-dialog";
import { PassCandidateDialog } from "@/components/candidate-search/pass-candidate-dialog";
import { RequestIntroductionDialog } from "@/components/candidate-search/request-introduction-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { useCandidateSearch } from "@/lib/queries/candidate-search";
import { useMyShadowJobs } from "@/lib/queries/shadow-jobs";
import { useBulkRequestTalentPool } from "@/lib/queries/talent-pool";

export default function SearchCandidatesPage() {
  const container = useThemeScopeContainer();
  const { data: jobs, isLoading: jobsLoading } = useMyShadowJobs();
  const [jobId, setJobId] = React.useState<string | undefined>(undefined);
  const { data: results, isLoading: searching } = useCandidateSearch(jobId, {
    enabled: !!jobId,
  });
  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const [bulkDialogOpen, setBulkDialogOpen] = React.useState(false);
  const [quickAddState, setQuickAddState] = React.useState<
    Record<string, { state: QuickTalentPoolState; skipReason?: string }>
  >({});
  const bulkRequest = useBulkRequestTalentPool();
  const [quickViewIndex, setQuickViewIndex] = React.useState<number | null>(null);
  const [passTarget, setPassTarget] = React.useState<string | null>(null);
  const [introTarget, setIntroTarget] = React.useState<string | null>(null);
  const [compareOpen, setCompareOpen] = React.useState(false);

  React.useEffect(() => {
    setSelected(new Set());
    setQuickAddState({});
    setQuickViewIndex(null);
    setPassTarget(null);
    setIntroTarget(null);
    setCompareOpen(false);
  }, [jobId]);

  const toggleSelected = (callsign: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(callsign)) next.delete(callsign);
      else next.add(callsign);
      return next;
    });
  };

  const handleQuickAdd = async (callsign: string) => {
    if (!jobId) return;
    setQuickAddState((prev) => ({ ...prev, [callsign]: { state: "pending" } }));
    try {
      const result = await bulkRequest.mutateAsync({ jobId, callsigns: [callsign] });
      if (result.requested.includes(callsign)) {
        setQuickAddState((prev) => ({ ...prev, [callsign]: { state: "added" } }));
      } else {
        const skip = result.skipped.find((s) => s.callsign === callsign);
        setQuickAddState((prev) => ({
          ...prev,
          [callsign]: { state: "skipped", skipReason: skip?.reason },
        }));
      }
    } catch {
      setQuickAddState((prev) => {
        const next = { ...prev };
        delete next[callsign];
        return next;
      });
    }
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

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="max-w-sm flex-1">
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
        {jobId && !searching && results && results.length > 0 && (
          <Button variant="secondary" size="sm" onClick={() => setQuickViewIndex(0)}>
            <Zap className="mr-1.5 h-3.5 w-3.5" />
            Shortlist Mode
          </Button>
        )}
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
                {selected.size >= 2 && (
                  <Button variant="secondary" size="sm" onClick={() => setCompareOpen(true)}>
                    <Columns3 className="mr-1.5 h-3.5 w-3.5" />
                    Compare ({Math.min(selected.size, 4)})
                  </Button>
                )}
                <Button variant="brand" size="sm" onClick={() => setBulkDialogOpen(true)}>
                  Save to Talent Pool
                </Button>
              </div>
            </div>
          )}
          {results.map((result, index) => (
            <CandidateSearchResultCard
              key={result.callsign}
              result={result}
              selected={selected.has(result.callsign)}
              onToggleSelected={() => toggleSelected(result.callsign)}
              talentPoolAction={{
                state: quickAddState[result.callsign]?.state ?? "idle",
                skipReason: quickAddState[result.callsign]?.skipReason,
                onAdd: () => void handleQuickAdd(result.callsign),
              }}
              onOpenQuickView={() => setQuickViewIndex(index)}
              onPass={() => setPassTarget(result.callsign)}
              onRequestIntroduction={() => setIntroTarget(result.callsign)}
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
          onDone={(result) => {
            setSelected(new Set());
            setQuickAddState((prev) => {
              const next = { ...prev };
              for (const callsign of result.requested) {
                next[callsign] = { state: "added" };
              }
              for (const skip of result.skipped) {
                next[skip.callsign] = { state: "skipped", skipReason: skip.reason };
              }
              return next;
            });
          }}
        />
      )}

      {results && (
        <CandidateQuickViewDialog
          open={quickViewIndex !== null}
          onOpenChange={(open) => {
            if (!open) setQuickViewIndex(null);
          }}
          result={quickViewIndex !== null ? (results[quickViewIndex] ?? null) : null}
          hasPrevious={quickViewIndex !== null && quickViewIndex > 0}
          hasNext={quickViewIndex !== null && quickViewIndex < results.length - 1}
          onPrevious={() => setQuickViewIndex((i) => (i !== null ? i - 1 : i))}
          onNext={() => setQuickViewIndex((i) => (i !== null ? i + 1 : i))}
          talentPoolAction={
            quickViewIndex !== null
              ? {
                  state: quickAddState[results[quickViewIndex]?.callsign ?? ""]?.state ?? "idle",
                  skipReason: quickAddState[results[quickViewIndex]?.callsign ?? ""]?.skipReason,
                  onAdd: () => void handleQuickAdd(results[quickViewIndex]!.callsign),
                }
              : undefined
          }
          onPass={
            quickViewIndex !== null
              ? () => {
                  // Closes Quick View before opening the Pass dialog -- two sibling Radix Dialog
                  // roots open at once causes each one's dismissable-layer outside-click
                  // detection to misfire and close both.
                  setPassTarget(results[quickViewIndex]!.callsign);
                  setQuickViewIndex(null);
                }
              : undefined
          }
          onRequestIntroduction={
            quickViewIndex !== null
              ? () => {
                  setIntroTarget(results[quickViewIndex]!.callsign);
                  setQuickViewIndex(null);
                }
              : undefined
          }
        />
      )}

      {jobId && passTarget && (
        <PassCandidateDialog
          open={!!passTarget}
          onOpenChange={(open) => {
            if (!open) setPassTarget(null);
          }}
          jobId={jobId}
          callsign={passTarget}
          onDone={() => {
            setQuickViewIndex(null);
            setPassTarget(null);
          }}
        />
      )}

      {jobId && introTarget && (
        <RequestIntroductionDialog
          open={!!introTarget}
          onOpenChange={(open) => {
            if (!open) setIntroTarget(null);
          }}
          jobId={jobId}
          callsign={introTarget}
          onDone={() => setIntroTarget(null)}
        />
      )}

      {results && (
        <CandidateCompareDialog
          open={compareOpen}
          onOpenChange={setCompareOpen}
          results={results.filter((r) => selected.has(r.callsign)).slice(0, 4)}
          totalSelected={selected.size}
          talentPoolActionFor={(callsign) => ({
            state: quickAddState[callsign]?.state ?? "idle",
            skipReason: quickAddState[callsign]?.skipReason,
            onAdd: () => void handleQuickAdd(callsign),
          })}
          onPass={(callsign) => {
            // Same close-other-dialog-first discipline as Quick View -- two sibling Radix
            // Dialog roots open at once breaks each one's outside-click dismissal.
            setPassTarget(callsign);
            setCompareOpen(false);
          }}
          onRequestIntroduction={(callsign) => {
            setIntroTarget(callsign);
            setCompareOpen(false);
          }}
          onRemove={toggleSelected}
        />
      )}
    </div>
  );
}
