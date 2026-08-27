"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Bookmark, BookmarkCheck, Briefcase, MapPin } from "lucide-react";

import { ApplyDisclosureDialog } from "@/components/candidate/apply-disclosure-dialog";
import { DimensionBreakdownList } from "@/components/dimension-breakdown-list";
import { FormattedText } from "@/components/formatted-text";
import { ShadowAppShell } from "@/components/shadow/shadow-app-shell";
import { useShadowCopilot } from "@/components/shadow/shadow-copilot-provider";
import { MatchToneList } from "@/components/shadow/match-tone-list";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { API_URL, ApiError } from "@/lib/api-client";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { formatSalary } from "@/lib/format";
import { useCompanyProfile } from "@/lib/queries/company";
import { useJobMatch } from "@/lib/queries/passport-matching";
import { useSaveJob, useSavedJobs, useUnsaveJob } from "@/lib/queries/saved-jobs";
import { useApplyToShadowJob, useShadowBoardJob } from "@/lib/queries/shadow-jobs";
import {
  EMPLOYMENT_TYPE_LABEL,
  MATCH_TIER_VARIANT,
  REMOTE_PREFERENCE_LABEL,
} from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";

export default function ShadowJobDetailPage() {
  const params = useParams<{ jobId: string }>();
  const router = useRouter();
  const { candidate, isLoading: authLoading } = useCandidateAuth();
  const { data: job, isLoading } = useShadowBoardJob(params.jobId);
  const { data: companyProfile } = useCompanyProfile(job?.company_slug ?? undefined);
  const applyMutation = useApplyToShadowJob(params.jobId);
  const { data: savedJobs } = useSavedJobs({ enabled: !!candidate });
  const isSaved = !!savedJobs?.some((saved) => saved.job.id === params.jobId);
  const saveJob = useSaveJob();
  const unsaveJob = useUnsaveJob();
  const { data: match } = useJobMatch(params.jobId, { enabled: !!candidate });
  const [applyError, setApplyError] = React.useState<string | null>(null);
  const [applied, setApplied] = React.useState(false);
  const [disclosureOpen, setDisclosureOpen] = React.useState(false);
  // Portal target for ApplyDisclosureDialog so it renders inside the themed shell wrapper instead
  // of document.body — see DialogContent's comment in dialog.tsx.
  const themeScopeContainer = useThemeScopeContainer();
  const { setContext } = useShadowCopilot();

  React.useEffect(() => {
    setContext({ type: "job", id: params.jobId });
    return () => setContext({ type: "none" });
  }, [params.jobId, setContext]);

  const handleApplyClick = () => {
    setApplyError(null);
    if (!candidate) {
      router.push("/shadow/signup");
      return;
    }
    setDisclosureOpen(true);
  };

  const handleConfirmApply = async () => {
    try {
      await applyMutation.mutateAsync();
      setDisclosureOpen(false);
      setApplied(true);
    } catch (err) {
      setDisclosureOpen(false);
      if (err instanceof ApiError && err.status === 400) {
        // Covers both "no Passport yet" and "Passport not approved" — the backend's own detail
        // message already says which, no need to guess client-side.
        setApplyError(err.detail);
      } else if (err instanceof ApiError && err.status === 409) {
        setApplyError("You've already applied to this role.");
      } else {
        setApplyError("Couldn't submit your application. Try again.");
      }
    }
  };

  const salary = job ? formatSalary(job.salary_min, job.salary_max) : null;

  return (
    <ShadowAppShell mainClassName="max-w-4xl rounded-2xl bg-card">
      {(isLoading || authLoading) && (
          <div className="flex justify-center py-16">
            <Spinner className="h-6 w-6 text-muted-foreground" />
          </div>
        )}

        {!isLoading && !job && (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              This role isn&apos;t open for applications anymore.
            </CardContent>
          </Card>
        )}

        {job && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-xl border border-border bg-card">
                  {companyProfile?.logo_url ? (
                    <Image
                      src={`${API_URL}${companyProfile.logo_url}`}
                      alt={`${job.company_name} logo`}
                      fill
                      className="object-contain"
                      unoptimized
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-base font-semibold text-muted-foreground">
                      {job.company_name.charAt(0).toUpperCase()}
                    </div>
                  )}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-foreground">
                    {job.company_name}
                  </p>
                  {job.company_slug && (
                    <Link
                      href={`/shadow/companies/${job.company_slug}`}
                      className="text-xs text-brand underline-offset-2 hover:underline"
                    >
                      View company profile
                    </Link>
                  )}
                </div>
              </div>

              <div className="flex items-start justify-between gap-4">
                <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                  {job.title}
                </h1>
                {candidate && (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    className="shrink-0"
                    onClick={() =>
                      isSaved ? unsaveJob.mutate(job.id) : saveJob.mutate({ shadowJobId: job.id })
                    }
                    disabled={saveJob.isPending || unsaveJob.isPending}
                  >
                    {isSaved ? (
                      <>
                        <BookmarkCheck className="h-4 w-4 text-brand" /> Saved
                      </>
                    ) : (
                      <>
                        <Bookmark className="h-4 w-4" /> Save
                      </>
                    )}
                  </Button>
                )}
              </div>
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
                  <Badge variant="outline">{REMOTE_PREFERENCE_LABEL[job.remote_preference]}</Badge>
                )}
                {job.seniority && <Badge variant="neutral">{job.seniority}</Badge>}
                {salary && <Badge variant="success">{salary}</Badge>}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_280px]">
              <Card>
                <CardContent className="flex flex-col gap-4 py-6">
                  <FormattedText text={job.description} className="text-sm text-foreground" />
                  {job.requirements.length > 0 && (
                    <div className="flex flex-col gap-2">
                      <h3 className="text-sm font-semibold text-foreground">Requirements</h3>
                      <ul className="list-inside list-disc text-sm text-muted-foreground">
                        {job.requirements.map((req, i) => (
                          <li key={i}>{req}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>

              <div className="flex flex-col gap-6 lg:sticky lg:top-24 lg:self-start">
                {match && (
                  <Card>
                    <CardContent className="flex flex-col gap-3 py-5">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          Why this matches
                        </p>
                        <Badge variant={MATCH_TIER_VARIANT[match.match_tier]}>
                          {match.match_tier}
                        </Badge>
                      </div>
                      <p className="text-sm text-foreground">{match.summary}</p>
                      <MatchToneList title="Strengths" items={match.strengths} tone="positive" />
                      <MatchToneList title="Gaps" items={match.gaps} tone="caution" />
                      <DimensionBreakdownList dimensions={match.dimension_breakdown} />
                    </CardContent>
                  </Card>
                )}
                <Card>
                  <CardContent className="flex flex-col gap-3 py-5">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      About this role
                    </p>
                    <dl className="flex flex-col gap-2.5 text-sm">
                      {job.location && (
                        <div className="flex items-center justify-between gap-3">
                          <dt className="text-muted-foreground">Location</dt>
                          <dd className="text-foreground">{job.location}</dd>
                        </div>
                      )}
                      <div className="flex items-center justify-between gap-3">
                        <dt className="text-muted-foreground">Type</dt>
                        <dd className="text-foreground">{EMPLOYMENT_TYPE_LABEL[job.employment_type]}</dd>
                      </div>
                      {job.remote_preference && (
                        <div className="flex items-center justify-between gap-3">
                          <dt className="text-muted-foreground">Remote</dt>
                          <dd className="text-foreground">
                            {REMOTE_PREFERENCE_LABEL[job.remote_preference]}
                          </dd>
                        </div>
                      )}
                      {job.seniority && (
                        <div className="flex items-center justify-between gap-3">
                          <dt className="text-muted-foreground">Seniority</dt>
                          <dd className="text-foreground">{job.seniority}</dd>
                        </div>
                      )}
                      {salary && (
                        <div className="flex items-center justify-between gap-3">
                          <dt className="text-muted-foreground">Salary</dt>
                          <dd className="text-foreground">{salary}</dd>
                        </div>
                      )}
                    </dl>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="flex flex-col items-start gap-3 py-6">
                    {applied ? (
                      <p className="text-sm font-medium text-success">
                        Application submitted. Track its status from your Applications page.
                      </p>
                    ) : (
                      <>
                        <p className="text-sm text-muted-foreground">
                          One-click apply with whatever your Phantom Passport already holds.
                          Nothing new to fill in.
                        </p>
                        {applyError && <p className="text-sm font-medium text-danger">{applyError}</p>}
                        <Button
                          variant="brand"
                          size="lg"
                          className="w-full"
                          onClick={handleApplyClick}
                          disabled={applyMutation.isPending}
                        >
                          {applyMutation.isPending
                            ? "Applying…"
                            : candidate
                              ? "Apply with Phantom Passport"
                              : "Sign up to apply"}
                        </Button>
                      </>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        )}
      <ApplyDisclosureDialog
        open={disclosureOpen}
        onOpenChange={setDisclosureOpen}
        onConfirm={handleConfirmApply}
        isSubmitting={applyMutation.isPending}
        container={themeScopeContainer}
      />
    </ShadowAppShell>
  );
}
