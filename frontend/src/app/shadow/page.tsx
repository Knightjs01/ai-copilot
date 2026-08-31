"use client";

import * as React from "react";
import Link from "next/link";
import { Briefcase, SearchX } from "lucide-react";

import { EmptyState } from "@/components/shadow/empty-state";
import { ShadowAppShell } from "@/components/shadow/shadow-app-shell";
import { ShadowBoardToolbar } from "@/components/shadow/shadow-board-toolbar";
import { ShadowJobCard } from "@/components/shadow/shadow-job-card";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useCreateJobAlert } from "@/lib/queries/job-alerts";
import { useBatchJobMatches, useNlJobSearch } from "@/lib/queries/passport-matching";
import { useMyPassport } from "@/lib/queries/phantom-passport";
import { useSaveJob, useSavedJobs, useUnsaveJob } from "@/lib/queries/saved-jobs";
import { useShadowBoard } from "@/lib/queries/shadow-jobs";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import type { EmploymentType, RemotePreference } from "@/lib/types";

const MAX_MATCH_BATCH = 24;

export default function ShadowBoardPage() {
  const [search, setSearch] = React.useState("");
  const [remotePreference, setRemotePreference] = React.useState<RemotePreference | "all">("all");
  const [employmentType, setEmploymentType] = React.useState<EmploymentType | "all">("all");
  const [location, setLocation] = React.useState("");
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

  return (
    <ShadowAppShell mainClassName="max-w-4xl">
      <div className="mb-8 flex flex-col gap-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            The job market you can enter without being seen
          </p>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            Shadow - Anonymous Talent Network
          </h1>
          <p className="max-w-xl text-sm text-muted-foreground">
            Apply with your Phantom Passport. Companies see your skills and experience, not your
            name, until you choose to reveal it. Every open role is listed here, unranked — filter
            or search to narrow it down.
          </p>
          {!candidate ? (
            <p className="text-sm text-muted-foreground">
              Want these roles ranked by fit?{" "}
              <Link href="/shadow/login" className="font-medium text-brand hover:underline">
                Log in and build a Phantom Passport
              </Link>{" "}
              to see them on For You.
            </p>
          ) : !passportApproved ? (
            <p className="text-sm text-muted-foreground">
              <Link href="/shadow/passport" className="font-medium text-brand hover:underline">
                Finish your Phantom Passport
              </Link>{" "}
              to unlock a ranked shortlist of these same roles.
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">
              See these same roles{" "}
              <Link href="/shadow/for-you" className="font-medium text-brand hover:underline">
                ranked by fit for you on For You
              </Link>
              .
            </p>
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
            matchCount={filteredJobs.length}
            totalCount={jobs?.length ?? 0}
            container={themeScopeContainer}
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

        {isLoading && (
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
    </ShadowAppShell>
  );
}
