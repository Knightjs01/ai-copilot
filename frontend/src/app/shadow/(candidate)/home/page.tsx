"use client";

import * as React from "react";
import Link from "next/link";
import { Bookmark, Briefcase, IdCard, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useBatchJobMatches } from "@/lib/queries/passport-matching";
import { useSavedJobs } from "@/lib/queries/saved-jobs";
import { useMyApplications, useShadowBoard } from "@/lib/queries/shadow-jobs";
import { useMyPassport } from "@/lib/queries/phantom-passport";
import { MATCH_TIER_VARIANT } from "@/lib/status-display";
import type { ShadowJobBoardListing } from "@/lib/types";

const TERMINAL_STATUSES = new Set(["declined", "withdrawn"]);
const HOME_MATCH_PREVIEW = 24;
const TOP_MATCHES_SHOWN = 3;

// Built from data that's real today -- Passport completion, active application count, saved job
// count, and (once a Passport is approved) the top real AI matches from the board. See
// passport_matching for the matching engine this section is built on.
export default function ShadowHomePage() {
  const { candidate } = useCandidateAuth();
  const { data: passport, isLoading: isLoadingPassport } = useMyPassport();
  const { data: applications, isLoading: isLoadingApplications } = useMyApplications();
  const { data: savedJobs, isLoading: isLoadingSaved } = useSavedJobs();

  const isLoading = isLoadingPassport || isLoadingApplications || isLoadingSaved;

  const activeApplicationsCount =
    applications?.filter((application) => !TERMINAL_STATUSES.has(application.status)).length ?? 0;
  const savedJobsCount = savedJobs?.length ?? 0;
  const completionPercentage = passport?.completion_percentage ?? 0;
  const passportApproved = passport?.current_version_number != null;

  const { data: boardJobs } = useShadowBoard();
  const previewJobIds = (boardJobs ?? []).slice(0, HOME_MATCH_PREVIEW).map((job) => job.id);
  const { data: matches } = useBatchJobMatches(previewJobIds, { enabled: passportApproved });
  const topMatches = React.useMemo(() => {
    if (!boardJobs || !matches) return [];
    const jobById = new Map(boardJobs.map((job) => [job.id, job]));
    const entries: { match: (typeof matches)[number]; job: ShadowJobBoardListing }[] = [];
    for (const match of matches) {
      const job = jobById.get(match.job_id);
      if (job) entries.push({ match, job });
    }
    return entries.sort((a, b) => b.match.match_score - a.match.match_score).slice(0, TOP_MATCHES_SHOWN);
  }, [boardJobs, matches]);

  const subheading = !passport
    ? "Build your Phantom Passport to start discovering opportunities."
    : !passportApproved
      ? "Finish and approve your Passport to start applying."
      : activeApplicationsCount > 0
        ? `You have ${activeApplicationsCount} active application${activeApplicationsCount === 1 ? "" : "s"}.`
        : "Browse Discover to find your next opportunity.";

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {candidate ? `Good to see you, ${candidate.first_name}.` : "Welcome back."}
        </h1>
        <p className="text-sm text-muted-foreground">{subheading}</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Link href="/shadow/passport">
              <Card className="h-full transition-colors hover:border-brand/40">
                <CardContent className="flex flex-col gap-2 py-6">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <IdCard className="h-4 w-4" />
                    <span className="text-xs font-medium uppercase tracking-wide">Passport</span>
                  </div>
                  <span className="text-2xl font-semibold text-foreground">
                    {completionPercentage}%
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {passportApproved ? "Approved" : "Complete"}
                  </span>
                </CardContent>
              </Card>
            </Link>

            <Link href="/shadow/applications">
              <Card className="h-full transition-colors hover:border-brand/40">
                <CardContent className="flex flex-col gap-2 py-6">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Briefcase className="h-4 w-4" />
                    <span className="text-xs font-medium uppercase tracking-wide">
                      Active applications
                    </span>
                  </div>
                  <span className="text-2xl font-semibold text-foreground">
                    {activeApplicationsCount}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {activeApplicationsCount === 1 ? "In progress" : "In progress"}
                  </span>
                </CardContent>
              </Card>
            </Link>

            <Link href="/shadow/saved-jobs">
              <Card className="h-full transition-colors hover:border-brand/40">
                <CardContent className="flex flex-col gap-2 py-6">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Bookmark className="h-4 w-4" />
                    <span className="text-xs font-medium uppercase tracking-wide">Saved jobs</span>
                  </div>
                  <span className="text-2xl font-semibold text-foreground">{savedJobsCount}</span>
                  <span className="text-xs text-muted-foreground">
                    {savedJobsCount === 1 ? "Role saved" : "Roles saved"}
                  </span>
                </CardContent>
              </Card>
            </Link>
          </div>

          {passportApproved && topMatches.length > 0 && (
            <Card>
              <CardContent className="flex flex-col gap-4 py-6">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-brand" />
                    <h2 className="text-sm font-semibold text-foreground">Your top matches</h2>
                  </div>
                  <Link
                    href="/shadow/for-you"
                    className="text-xs font-medium text-brand hover:underline"
                  >
                    See all matches
                  </Link>
                </div>
                <div className="flex flex-col gap-2.5">
                  {topMatches.map(({ job, match }) => (
                    <Link
                      key={job.id}
                      href={`/shadow/jobs/${job.id}`}
                      className="flex items-center justify-between gap-3 rounded-xl border border-border px-3.5 py-2.5 transition-colors hover:border-brand/40"
                    >
                      <div className="flex flex-col gap-0.5">
                        <span className="text-sm font-medium text-foreground">{job.title}</span>
                        <span className="text-xs text-muted-foreground">{job.company_name}</span>
                      </div>
                      <Badge variant={MATCH_TIER_VARIANT[match.match_tier]}>
                        {match.match_tier}
                      </Badge>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {!passportApproved && (
            <Card>
              <CardContent className="flex flex-col items-start gap-3 py-6 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex flex-col gap-0.5">
                  <h2 className="text-sm font-semibold text-foreground">
                    {passport ? "Your Passport isn't approved yet" : "You haven't built a Passport yet"}
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    Nothing becomes visible to a company until you review and approve it.
                  </p>
                </div>
                <Button asChild variant="brand">
                  <Link href="/shadow/passport">
                    {passport ? "Finish your Passport" : "Build your Passport"}
                  </Link>
                </Button>
              </CardContent>
            </Card>
          )}

          {passportApproved && activeApplicationsCount === 0 && (
            <Card>
              <CardContent className="flex flex-col items-start gap-3 py-6 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex flex-col gap-0.5">
                  <h2 className="text-sm font-semibold text-foreground">Nothing applied to yet</h2>
                  <p className="text-sm text-muted-foreground">
                    Browse open roles and apply in seconds with your Passport.
                  </p>
                </div>
                <Button asChild variant="brand">
                  <Link href="/shadow">Discover roles</Link>
                </Button>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
