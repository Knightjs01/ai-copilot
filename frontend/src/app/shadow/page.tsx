"use client";

import * as React from "react";
import Link from "next/link";
import { Bookmark, BookmarkCheck, Briefcase, MapPin, SearchX } from "lucide-react";

import { ShadowBoardToolbar } from "@/components/shadow/shadow-board-toolbar";
import { ShadowTopNav } from "@/components/shadow/shadow-top-nav";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useCreateJobAlert } from "@/lib/queries/job-alerts";
import { useBatchJobMatches, useNlJobSearch } from "@/lib/queries/passport-matching";
import { useSaveJob, useSavedJobs, useUnsaveJob } from "@/lib/queries/saved-jobs";
import { useShadowBoard } from "@/lib/queries/shadow-jobs";
import {
  EMPLOYMENT_TYPE_LABEL,
  MATCH_TIER_VARIANT,
  REMOTE_PREFERENCE_LABEL,
} from "@/lib/status-display";
import type { EmploymentType, RemotePreference } from "@/lib/types";
import styles from "./shadow-theme.module.css";

const MAX_MATCH_BATCH = 24;

const MAX_REQUIREMENT_TAGS = 2;

function formatSalary(min: number | null, max: number | null): string | null {
  if (!min && !max) return null;
  const fmt = (n: number) => `£${(n / 1000).toFixed(0)}k`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  return fmt((min ?? max)!);
}

export default function ShadowBoardPage() {
  const [search, setSearch] = React.useState("");
  const [remotePreference, setRemotePreference] = React.useState<RemotePreference | "all">("all");
  const [employmentType, setEmploymentType] = React.useState<EmploymentType | "all">("all");
  // No visible Select for this today (see shadow-board-toolbar.tsx) -- the real board endpoint
  // supports it, but the only way to set it right now is via Ask Phantom's parsed NL query.
  const [location, setLocation] = React.useState<string | null>(null);
  const mainRef = React.useRef<HTMLElement>(null);
  const { candidate } = useCandidateAuth();

  const { data: jobs, isLoading } = useShadowBoard({
    remote_preference: remotePreference === "all" ? undefined : remotePreference,
    employment_type: employmentType === "all" ? undefined : employmentType,
    location: location ?? undefined,
  });

  const { data: savedJobs } = useSavedJobs({ enabled: !!candidate });
  const savedJobIds = React.useMemo(
    () => new Set(savedJobs?.map((saved) => saved.job.id)),
    [savedJobs]
  );
  const saveJob = useSaveJob();
  const unsaveJob = useUnsaveJob();

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
  // catalog, per Phase 2's cost-bounding call (see the Shadow Phase 2 plan).
  const matchJobIds = React.useMemo(
    () => filteredJobs.slice(0, MAX_MATCH_BATCH).map((job) => job.id),
    [filteredJobs]
  );
  const { data: matches } = useBatchJobMatches(matchJobIds, { enabled: !!candidate });
  const matchByJobId = React.useMemo(
    () => new Map((matches ?? []).map((match) => [match.job_id, match])),
    [matches]
  );

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

  return (
    // ShadowTopNav + this outer bg-slate-50 gutter stay light. Only <main> (the actual board
    // content) goes obsidian/blue — Shadow keeps its own distinct dark theme, separate from
    // Passport's, per the user's explicit call to not merge the two.
    <div className="min-h-screen bg-slate-50">
      <ShadowTopNav />
      <main ref={mainRef} className={`${styles.shadowTheme} mx-auto max-w-4xl rounded-2xl px-6 py-10`}>
        <div className="mb-8 flex flex-col gap-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            The job market you can enter without being seen
          </p>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            The Shadow job board
          </h1>
          <p className="max-w-xl text-sm text-muted-foreground">
            Apply with your Phantom Passport. Companies see your skills and experience, not your
            name, until you choose to reveal it.
          </p>
        </div>

        <div className="mb-6">
          <ShadowBoardToolbar
            search={search}
            onSearchChange={setSearch}
            remotePreference={remotePreference}
            onRemotePreferenceChange={setRemotePreference}
            employmentType={employmentType}
            onEmploymentTypeChange={setEmploymentType}
            matchCount={filteredJobs.length}
            totalCount={jobs?.length ?? 0}
            container={mainRef.current}
            canAskPhantom={!!candidate}
            onAskPhantom={handleAskPhantom}
            isAskPhantomPending={nlSearch.isPending}
            onSaveSearch={candidate ? handleSaveSearch : undefined}
            isSaveSearchPending={createJobAlert.isPending}
          />
          {saveSearchMessage && (
            <p
              className={`mt-2 text-xs ${createJobAlert.isError ? "text-danger" : "text-success"}`}
            >
              {saveSearchMessage}
            </p>
          )}
        </div>

        {location && (
          <div className="mb-6 -mt-3 flex items-center gap-2">
            <Badge variant="outline" className="gap-1.5">
              Location: {location}
              <button
                type="button"
                onClick={() => setLocation(null)}
                aria-label="Clear location filter"
                className="text-muted-foreground hover:text-foreground"
              >
                ×
              </button>
            </Badge>
          </div>
        )}

        {isLoading && (
          <div className="flex justify-center py-16">
            <Spinner className="h-6 w-6 text-muted-foreground" />
          </div>
        )}

        {!isLoading && jobs?.length === 0 && (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              No open roles right now. Check back soon.
            </CardContent>
          </Card>
        )}

        {!isLoading && (jobs?.length ?? 0) > 0 && filteredJobs.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
              <SearchX className="h-5 w-5 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No roles match your search right now.</p>
            </CardContent>
          </Card>
        )}

        <div className="flex flex-col gap-3">
          {filteredJobs.map((job) => {
            const salary = formatSalary(job.salary_min, job.salary_max);
            const extraRequirements = job.requirements.length - MAX_REQUIREMENT_TAGS;
            const isSaved = savedJobIds.has(job.id);
            const match = matchByJobId.get(job.id);
            return (
              <Card key={job.id} className="relative transition-colors hover:border-muted-foreground/40">
                {candidate && (
                  <button
                    type="button"
                    onClick={() =>
                      isSaved ? unsaveJob.mutate(job.id) : saveJob.mutate({ shadowJobId: job.id })
                    }
                    disabled={saveJob.isPending || unsaveJob.isPending}
                    className="absolute right-4 top-4 z-10 flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                    aria-label={isSaved ? "Remove from saved jobs" : "Save this job"}
                  >
                    {isSaved ? (
                      <BookmarkCheck className="h-4 w-4 text-brand" />
                    ) : (
                      <Bookmark className="h-4 w-4" />
                    )}
                  </button>
                )}
                <CardContent className="flex flex-col gap-2.5 py-5">
                  <Link href={`/shadow/jobs/${job.id}`} className="flex flex-col gap-2.5">
                    <div className="flex items-start justify-between gap-4 pr-8">
                      <div className="flex flex-col gap-0.5">
                        <h2 className="text-base font-semibold text-foreground">{job.title}</h2>
                        <p className="text-sm text-muted-foreground">{job.company_name}</p>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-1.5">
                        {match && (
                          <Badge variant={MATCH_TIER_VARIANT[match.match_tier]}>
                            {match.match_tier}
                          </Badge>
                        )}
                        {salary && <Badge variant="success">{salary}</Badge>}
                      </div>
                    </div>
                    <p className="line-clamp-2 text-sm text-muted-foreground">{job.summary}</p>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                      {job.location && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5" />
                          {job.location}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Briefcase className="h-3.5 w-3.5" />
                        {EMPLOYMENT_TYPE_LABEL[job.employment_type]}
                      </span>
                      {job.remote_preference && (
                        <Badge variant="outline">
                          {REMOTE_PREFERENCE_LABEL[job.remote_preference]}
                        </Badge>
                      )}
                      {job.seniority && <Badge variant="neutral">{job.seniority}</Badge>}
                    </div>
                    {job.requirements.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5">
                        {job.requirements.slice(0, MAX_REQUIREMENT_TAGS).map((req) => (
                          <span
                            key={req}
                            className="rounded-full border border-border bg-secondary/40 px-2.5 py-0.5 text-[11px] text-foreground/80"
                          >
                            {req}
                          </span>
                        ))}
                        {extraRequirements > 0 && (
                          <span className="text-[11px] text-muted-foreground">
                            +{extraRequirements} more
                          </span>
                        )}
                      </div>
                    )}
                  </Link>
                  {job.company_slug && (
                    <Link
                      href={`/shadow/companies/${job.company_slug}`}
                      className="w-fit text-xs text-brand underline-offset-2 hover:underline"
                    >
                      View company profile
                    </Link>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </main>
    </div>
  );
}
