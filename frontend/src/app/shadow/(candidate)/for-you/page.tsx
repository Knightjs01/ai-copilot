"use client";

import * as React from "react";
import Link from "next/link";
import { Sparkles, Undo2 } from "lucide-react";

import { EmptyState } from "@/components/shadow/empty-state";
import { JobMatchCard } from "@/components/shadow/job-match-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useDismissedJobIds, useDismissJob, useUndismissJob } from "@/lib/queries/dismissed-jobs";
import { useBatchJobMatches } from "@/lib/queries/passport-matching";
import { useMyPassport } from "@/lib/queries/phantom-passport";
import { useSavedJobs, useSaveJob, useUnsaveJob } from "@/lib/queries/saved-jobs";
import { useShadowBoard } from "@/lib/queries/shadow-jobs";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import type { ShadowJobBoardListing, ShadowJobMatch } from "@/lib/types";

const MAX_MATCH_BATCH = 24;

type SortOption = "best_match" | "newest" | "salary_desc";

function sortRanked(
  ranked: { job: ShadowJobBoardListing; match: ShadowJobMatch }[],
  sort: SortOption
) {
  const copy = [...ranked];
  if (sort === "newest") {
    return copy.sort(
      (a, b) => new Date(b.job.published_at ?? 0).getTime() - new Date(a.job.published_at ?? 0).getTime()
    );
  }
  if (sort === "salary_desc") {
    return copy.sort(
      (a, b) => (b.job.salary_max ?? b.job.salary_min ?? 0) - (a.job.salary_max ?? a.job.salary_min ?? 0)
    );
  }
  return copy.sort((a, b) => b.match.match_score - a.match.match_score);
}

// Requires an approved Passport, unlike Discover which works for anyone -- there's no valid
// match cache key before that (see backend passport_matching/__init__.py). Sorted by match_score
// descending by default, capped at the same batch size the board uses for its own badges.
export default function ShadowForYouPage() {
  const themeScopeContainer = useThemeScopeContainer();
  const [sort, setSort] = React.useState<SortOption>("best_match");
  const [justDismissed, setJustDismissed] = React.useState<{ id: string; title: string } | null>(
    null
  );
  const undoTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const { data: passport, isLoading: isLoadingPassport } = useMyPassport();
  const passportApproved = passport?.current_version_number != null;

  const { data: jobs, isLoading: isLoadingJobs } = useShadowBoard();
  const jobIds = React.useMemo(
    () => (jobs ?? []).slice(0, MAX_MATCH_BATCH).map((job) => job.id),
    [jobs]
  );
  const { data: matches, isLoading: isLoadingMatches } = useBatchJobMatches(jobIds, {
    enabled: passportApproved,
  });
  const { data: savedJobs } = useSavedJobs();
  const { data: dismissedIds } = useDismissedJobIds();
  const saveJob = useSaveJob();
  const unsaveJob = useUnsaveJob();
  const dismissJob = useDismissJob();
  const undismissJob = useUndismissJob();

  const savedJobIds = React.useMemo(
    () => new Set((savedJobs ?? []).map((s) => s.job.id)),
    [savedJobs]
  );
  const dismissedSet = React.useMemo(() => new Set(dismissedIds ?? []), [dismissedIds]);

  const rankedJobs = React.useMemo(() => {
    if (!jobs || !matches) return [];
    const matchByJobId = new Map(matches.map((match) => [match.job_id, match]));
    const ranked = jobs
      .filter((job) => matchByJobId.has(job.id) && !dismissedSet.has(job.id))
      .map((job) => ({ job, match: matchByJobId.get(job.id)! }));
    return sortRanked(ranked, sort);
  }, [jobs, matches, dismissedSet, sort]);

  function handleDismiss(job: ShadowJobBoardListing) {
    dismissJob.mutate(job.id);
    if (undoTimerRef.current) clearTimeout(undoTimerRef.current);
    setJustDismissed({ id: job.id, title: job.title });
    undoTimerRef.current = setTimeout(() => setJustDismissed(null), 6000);
  }

  function handleUndo() {
    if (!justDismissed) return;
    if (undoTimerRef.current) clearTimeout(undoTimerRef.current);
    undismissJob.mutate(justDismissed.id);
    setJustDismissed(null);
  }

  const isLoading = isLoadingPassport || (passportApproved && (isLoadingJobs || isLoadingMatches));

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">For you</h1>
        <p className="text-sm text-muted-foreground">
          The same open roles as Discover, ranked by how well they match your Phantom Passport.
        </p>
        <p className="text-sm text-muted-foreground">
          Prefer to browse everything yourself?{" "}
          <Link href="/shadow" className="font-medium text-brand hover:underline">
            See Discover.
          </Link>
        </p>
      </div>

      {isLoadingPassport ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      ) : !passportApproved ? (
        <Card>
          <CardContent className="flex flex-col items-start gap-3 py-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-col gap-0.5">
              <h2 className="text-sm font-semibold text-foreground">
                {passport ? "Your Passport isn't approved yet" : "You haven't built a Passport yet"}
              </h2>
              <p className="text-sm text-muted-foreground">
                Build and approve your Phantom Passport to unlock AI-matched roles. In the
                meantime, browse every open role on{" "}
                <Link href="/shadow" className="font-medium text-brand hover:underline">
                  Discover
                </Link>
                .
              </p>
            </div>
            <Button asChild variant="brand">
              <Link href="/shadow/passport">
                {passport ? "Finish your Passport" : "Build your Passport"}
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      ) : rankedJobs.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No matches yet"
          description="Check back once more roles are posted."
        />
      ) : (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            {justDismissed ? (
              <button
                type="button"
                onClick={handleUndo}
                className="flex items-center gap-1.5 text-xs font-medium text-brand hover:underline"
              >
                <Undo2 className="h-3.5 w-3.5" />
                Removed &ldquo;{justDismissed.title}&rdquo; &mdash; Undo
              </button>
            ) : (
              <span />
            )}
            <Select value={sort} onValueChange={(value) => setSort(value as SortOption)}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="Sort" />
              </SelectTrigger>
              <SelectContent container={themeScopeContainer}>
                <SelectItem value="best_match">Best match</SelectItem>
                <SelectItem value="newest">Newest</SelectItem>
                <SelectItem value="salary_desc">Salary: high to low</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {rankedJobs.map(({ job, match }, index) => (
            <JobMatchCard
              key={job.id}
              job={job}
              match={match}
              variant={index === 0 && sort === "best_match" ? "featured" : "compact"}
              saveAction={{
                saved: savedJobIds.has(job.id),
                pending: saveJob.isPending || unsaveJob.isPending,
                onToggle: () =>
                  savedJobIds.has(job.id)
                    ? unsaveJob.mutate(job.id)
                    : saveJob.mutate({ shadowJobId: job.id }),
              }}
              onDismiss={() => handleDismiss(job)}
            />
          ))}
        </div>
      )}

      <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Sparkles className="h-3.5 w-3.5" />
        Matches are computed by Phantom AI against your approved Passport and recompute
        automatically when either changes.
      </p>
    </div>
  );
}
