"use client";

import * as React from "react";
import Link from "next/link";
import { Briefcase, SearchX, Sparkles, Undo2 } from "lucide-react";

import { EmptyState } from "@/components/shadow/empty-state";
import { JobMatchCard } from "@/components/shadow/job-match-card";
import { ShadowAppShell } from "@/components/shadow/shadow-app-shell";
import { ShadowBoardToolbar } from "@/components/shadow/shadow-board-toolbar";
import { ShadowJobCard } from "@/components/shadow/shadow-job-card";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useDismissedJobIds, useDismissJob, useUndismissJob } from "@/lib/queries/dismissed-jobs";
import { useCreateJobAlert } from "@/lib/queries/job-alerts";
import { useBatchJobMatches, useNlJobSearch } from "@/lib/queries/passport-matching";
import { useMyPassport } from "@/lib/queries/phantom-passport";
import { useSaveJob, useSavedJobs, useUnsaveJob } from "@/lib/queries/saved-jobs";
import { useShadowBoard } from "@/lib/queries/shadow-jobs";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import type { EmploymentType, RemotePreference, ShadowJobBoardListing, ShadowJobMatch } from "@/lib/types";

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

// The single Shadow board destination — public/unranked browsing (search, location, remote/
// employment filters, Ask Phantom, Save-search) for anyone, layered with real match-based ranking
// (Sort, Dismiss/Undo, the richer JobMatchCard) once a candidate has an approved Phantom Passport.
// Previously two separate pages (Discover + For You); merged so ranking is a state on top of the
// same page rather than a second destination to navigate to.
export default function ShadowBoardPage() {
  const [search, setSearch] = React.useState("");
  const [remotePreference, setRemotePreference] = React.useState<RemotePreference | "all">("all");
  const [employmentType, setEmploymentType] = React.useState<EmploymentType | "all">("all");
  const [location, setLocation] = React.useState("");
  const [sort, setSort] = React.useState<SortOption>("best_match");
  const [justDismissed, setJustDismissed] = React.useState<{ id: string; title: string } | null>(
    null
  );
  const undoTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const themeScopeContainer = useThemeScopeContainer();
  const { candidate } = useCandidateAuth();
  const { data: passport } = useMyPassport({ enabled: !!candidate });
  const passportApproved = passport?.current_version_number != null;

  const { data: jobs, isLoading } = useShadowBoard({
    remote_preference: remotePreference === "all" ? undefined : remotePreference,
    employment_type: employmentType === "all" ? undefined : employmentType,
    location: location.trim() || undefined,
  });

  const { data: savedJobs } = useSavedJobs({ enabled: !!candidate });
  const savedJobIds = React.useMemo(
    () => new Set(savedJobs?.map((saved) => saved.job.id)),
    [savedJobs]
  );
  const saveJob = useSaveJob();
  const unsaveJob = useUnsaveJob();

  const { data: dismissedIds } = useDismissedJobIds({ enabled: passportApproved });
  const dismissedSet = React.useMemo(() => new Set(dismissedIds ?? []), [dismissedIds]);
  const dismissJob = useDismissJob();
  const undismissJob = useUndismissJob();

  const filteredJobs = React.useMemo(() => {
    if (!jobs) return [];
    const query = search.trim().toLowerCase();
    if (!query) return jobs;
    return jobs.filter(
      (job) =>
        job.title.toLowerCase().includes(query) ||
        job.summary.toLowerCase().includes(query) ||
        job.company_name.toLowerCase().includes(query)
    );
  }, [jobs, search]);

  // Only ever the currently-rendered, post-filter jobs, capped -- never the full unfiltered
  // catalog, per Phase 2's cost-bounding call (see the Shadow Phase 2 plan). Fetched for any
  // logged-in candidate (not gated on passport approval) so a badge preview can show even before
  // approval; the same result also feeds the ranked pipeline below once approved.
  const matchJobIds = React.useMemo(
    () => filteredJobs.slice(0, MAX_MATCH_BATCH).map((job) => job.id),
    [filteredJobs]
  );
  const { data: matches, isLoading: isLoadingMatches } = useBatchJobMatches(matchJobIds, {
    enabled: !!candidate,
  });
  const matchByJobId = React.useMemo(
    () => new Map((matches ?? []).map((match) => [match.job_id, match])),
    [matches]
  );

  const rankedJobs = React.useMemo(() => {
    if (!passportApproved) return [];
    const ranked = filteredJobs
      .filter((job) => matchByJobId.has(job.id) && !dismissedSet.has(job.id))
      .map((job) => ({ job, match: matchByJobId.get(job.id)! }));
    return sortRanked(ranked, sort);
  }, [passportApproved, filteredJobs, matchByJobId, dismissedSet, sort]);

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

  const nlSearch = useNlJobSearch();
  const handleAskPhantom = (query: string) => {
    nlSearch.mutate(query, {
      onSuccess: (filters) => {
        if (filters.remote_preference) {
          setRemotePreference(filters.remote_preference as RemotePreference);
        }
        if (filters.employment_type) {
          setEmploymentType(filters.employment_type as EmploymentType);
        }
        if (filters.location) setLocation(filters.location);
        // else leave the location input untouched -- a null/absent field in the NL result isn't
        // the same as the candidate explicitly clearing what they'd already typed.
      },
    });
  };

  const createJobAlert = useCreateJobAlert();
  const [saveSearchMessage, setSaveSearchMessage] = React.useState<string | null>(null);
  const handleSaveSearch = (name: string) => {
    setSaveSearchMessage(null);
    createJobAlert.mutate(
      {
        name: name || undefined,
        remote_preference: remotePreference === "all" ? undefined : remotePreference,
        employment_type: employmentType === "all" ? undefined : employmentType,
      },
      {
        onSuccess: () => setSaveSearchMessage("Alert saved — see it under Saved Jobs."),
        onError: () => setSaveSearchMessage("Couldn't save that alert. Try again."),
      }
    );
  };

  const waitingOnMatches = passportApproved && isLoadingMatches;
  const noFilterResults = passportApproved
    ? rankedJobs.length === 0
    : filteredJobs.length === 0;

  return (
    <ShadowAppShell mainClassName="max-w-4xl">
      <div className="mb-8 flex flex-col gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand">
          The job market you can enter without being seen
        </p>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Discover Roles
        </h1>
        <p className="max-w-xl text-sm text-muted-foreground">
          Apply with your Phantom Passport. Companies see your skills and experience, not your
          name, until you choose to reveal it.
        </p>
        {!candidate ? (
          <p className="text-sm text-muted-foreground">
            Want these roles ranked by fit?{" "}
            <Link href="/shadow/login" className="font-medium text-brand hover:underline">
              Log in and build a Phantom Passport
            </Link>
            .
          </p>
        ) : (
          !passportApproved && (
            <p className="text-sm text-muted-foreground">
              <Link href="/shadow/passport" className="font-medium text-brand hover:underline">
                Finish your Phantom Passport
              </Link>{" "}
              to unlock a ranked shortlist of these roles.
            </p>
          )
        )}
      </div>

      <div className="mb-6">
        <ShadowBoardToolbar
          search={search}
          onSearchChange={setSearch}
          remotePreference={remotePreference}
          onRemotePreferenceChange={setRemotePreference}
          employmentType={employmentType}
          onEmploymentTypeChange={setEmploymentType}
          location={location}
          onLocationChange={setLocation}
          matchCount={passportApproved ? rankedJobs.length : filteredJobs.length}
          totalCount={jobs?.length ?? 0}
          container={themeScopeContainer}
          canAskPhantom={!!candidate}
          onAskPhantom={handleAskPhantom}
          isAskPhantomPending={nlSearch.isPending}
          onSaveSearch={candidate ? handleSaveSearch : undefined}
          isSaveSearchPending={createJobAlert.isPending}
        />
        {saveSearchMessage && (
          <p className={`mt-2 text-xs ${createJobAlert.isError ? "text-danger" : "text-success"}`}>
            {saveSearchMessage}
          </p>
        )}
      </div>

      {(isLoading || waitingOnMatches) && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && jobs?.length === 0 && (
        <EmptyState
          icon={Briefcase}
          title="No roles published yet"
          description="Check back soon, or set up a Job Alert to hear about new roles first."
          action={{ label: "Set up a Job Alert", href: "/shadow/saved-jobs#alerts" }}
        />
      )}

      {!isLoading && !waitingOnMatches && (jobs?.length ?? 0) > 0 && noFilterResults && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
            <SearchX className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No roles match your search right now.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !waitingOnMatches && (jobs?.length ?? 0) > 0 && !noFilterResults && (
        <>
          {passportApproved ? (
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

              <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Sparkles className="h-3.5 w-3.5" />
                Matches are computed by Phantom AI against your approved Passport and recompute
                automatically when either changes.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {filteredJobs.map((job) => {
                const isSaved = savedJobIds.has(job.id);
                const match = matchByJobId.get(job.id);
                return (
                  <ShadowJobCard
                    key={job.id}
                    job={job}
                    match={match}
                    saveAction={
                      candidate
                        ? {
                            saved: isSaved,
                            onToggle: () =>
                              isSaved
                                ? unsaveJob.mutate(job.id)
                                : saveJob.mutate({ shadowJobId: job.id }),
                            pending: saveJob.isPending || unsaveJob.isPending,
                          }
                        : undefined
                    }
                  />
                );
              })}
            </div>
          )}
        </>
      )}
    </ShadowAppShell>
  );
}
