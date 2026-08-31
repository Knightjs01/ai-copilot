"use client";

import * as React from "react";
import Link from "next/link";
import { CheckCircle2, ChevronDown, Sparkles } from "lucide-react";

import { EmptyState } from "@/components/shadow/empty-state";
import { MatchDetailPanel } from "@/components/shadow/match-detail-panel";
import { ShadowJobCard } from "@/components/shadow/shadow-job-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useBatchJobMatches } from "@/lib/queries/passport-matching";
import { useMyPassport } from "@/lib/queries/phantom-passport";
import { useShadowBoard } from "@/lib/queries/shadow-jobs";
import type { ShadowJobBoardListing, ShadowJobMatch } from "@/lib/types";

const MAX_MATCH_BATCH = 24;

// Collapsed by default -- a full 6-dimension breakdown plus complete strengths/gaps lists for up
// to MAX_MATCH_BATCH ranked cards would be a wall of content on a page whose value is quick
// scannability of *why you're ranked where you are*. The always-visible top-strength line gives
// the at-a-glance signal; this toggle gives full richness on demand.
function ForYouMatchRow({
  job,
  match,
}: {
  job: ShadowJobBoardListing;
  match: ShadowJobMatch;
}) {
  const [expanded, setExpanded] = React.useState(false);

  return (
    <div className="flex flex-col gap-2">
      <ShadowJobCard
        job={job}
        match={match}
        description={match.summary}
        showSeniority={false}
        showRequirements={false}
        showCompanyLink={false}
      />
      {match.strengths[0] && (
        <p className="flex items-center gap-1.5 px-1 text-xs text-muted-foreground">
          <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success" />
          {match.strengths[0]}
        </p>
      )}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-fit items-center gap-1 px-1 text-xs font-medium text-brand hover:underline"
      >
        Why this matches
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${expanded ? "rotate-180" : ""}`} />
      </button>
      {expanded && (
        <div className="rounded-2xl border border-border bg-card p-4">
          <MatchDetailPanel match={match} />
        </div>
      )}
    </div>
  );
}

// Requires an approved Passport, unlike Discover which works for anyone -- there's no valid
// match cache key before that (see backend passport_matching/__init__.py). Sorted by match_score
// descending, capped at the same batch size the board uses for its own badges.
export default function ShadowForYouPage() {
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

  const rankedJobs = React.useMemo(() => {
    if (!jobs || !matches) return [];
    const matchByJobId = new Map(matches.map((match) => [match.job_id, match]));
    return jobs
      .filter((job) => matchByJobId.has(job.id))
      .map((job) => ({ job, match: matchByJobId.get(job.id)! }))
      .sort((a, b) => b.match.match_score - a.match.match_score);
  }, [jobs, matches]);

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
          {rankedJobs.map(({ job, match }) => (
            <ForYouMatchRow key={job.id} job={job} match={match} />
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
