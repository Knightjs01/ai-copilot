"use client";

import * as React from "react";
import Link from "next/link";
import { Briefcase, MapPin, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useBatchJobMatches } from "@/lib/queries/passport-matching";
import { useMyPassport } from "@/lib/queries/phantom-passport";
import { useShadowBoard } from "@/lib/queries/shadow-jobs";
import {
  EMPLOYMENT_TYPE_LABEL,
  MATCH_TIER_VARIANT,
  REMOTE_PREFERENCE_LABEL,
} from "@/lib/status-display";

const MAX_MATCH_BATCH = 24;

function formatSalary(min: number | null, max: number | null): string | null {
  if (!min && !max) return null;
  const fmt = (n: number) => `£${(n / 1000).toFixed(0)}k`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  return fmt((min ?? max)!);
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
          Open roles ranked by how well they match your Phantom Passport.
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
                Build and approve your Phantom Passport to unlock AI-matched roles.
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
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No matches yet. Check back once more roles are posted.
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {rankedJobs.map(({ job, match }) => {
            const salary = formatSalary(job.salary_min, job.salary_max);
            return (
              <Link key={job.id} href={`/shadow/jobs/${job.id}`}>
                <Card className="transition-colors hover:border-brand/40">
                  <CardContent className="flex flex-col gap-2.5 py-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex flex-col gap-0.5">
                        <h2 className="text-base font-semibold text-foreground">{job.title}</h2>
                        <p className="text-sm text-muted-foreground">{job.company_name}</p>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-1.5">
                        <Badge variant={MATCH_TIER_VARIANT[match.match_tier]}>
                          {match.match_tier}
                        </Badge>
                        {salary && <Badge variant="success">{salary}</Badge>}
                      </div>
                    </div>
                    <p className="line-clamp-2 text-sm text-muted-foreground">{match.summary}</p>
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
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
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
