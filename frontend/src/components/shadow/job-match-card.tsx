"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import {
  BadgeCheck,
  Bookmark,
  BookmarkCheck,
  Briefcase,
  CheckCircle2,
  ChevronDown,
  MapPin,
  Send,
  Share2,
  X,
} from "lucide-react";

import { ApplyDisclosureDialog } from "@/components/candidate/apply-disclosure-dialog";
import { MatchDetailPanel } from "@/components/shadow/match-detail-panel";
import { MatchScoreRing } from "@/components/shadow/match-score-ring";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { API_URL, ApiError } from "@/lib/api-client";
import { companyAvatar } from "@/lib/company-avatar";
import { formatSalary } from "@/lib/format";
import { useApplyToShadowJob } from "@/lib/queries/shadow-jobs";
import { EMPLOYMENT_TYPE_LABEL, REMOTE_PREFERENCE_LABEL } from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import type { ShadowJobBoardListing, ShadowJobMatch } from "@/lib/types";

const MAX_HIGHLIGHTS = 3;

interface SaveAction {
  saved: boolean;
  onToggle: () => void;
  pending?: boolean;
}

interface JobMatchCardProps {
  job: ShadowJobBoardListing;
  match: ShadowJobMatch;
  variant: "featured" | "compact";
  saveAction: SaveAction;
  onDismiss?: () => void;
}

async function shareJob(jobId: string, title: string, companyName: string) {
  const url = `${window.location.origin}/shadow/jobs/${jobId}`;
  if (navigator.share) {
    try {
      await navigator.share({ title: `${title} at ${companyName}`, url });
      return;
    } catch {
      // User cancelled the share sheet, or the browser refused it -- fall through to clipboard.
    }
  }
  await navigator.clipboard.writeText(url);
}

function CompanyLogo({
  job,
  size,
}: {
  job: ShadowJobBoardListing;
  size: number;
}) {
  const avatar = companyAvatar(job.company_name);
  if (job.logo_url) {
    return (
      <div
        className="relative shrink-0 overflow-hidden rounded-lg border border-border bg-card"
        style={{ width: size, height: size }}
      >
        <Image
          src={`${API_URL}${job.logo_url}`}
          alt=""
          fill
          className="object-contain"
          unoptimized
        />
      </div>
    );
  }
  return (
    <div
      className={`flex shrink-0 items-center justify-center rounded-lg text-sm font-semibold ${avatar.colorClassName}`}
      style={{ width: size, height: size }}
    >
      {avatar.initial}
    </div>
  );
}

export function JobMatchCard({ job, match, variant, saveAction, onDismiss }: JobMatchCardProps) {
  const [expanded, setExpanded] = React.useState(false);
  const [applied, setApplied] = React.useState(false);
  const [applyError, setApplyError] = React.useState<string | null>(null);
  const [disclosureOpen, setDisclosureOpen] = React.useState(false);
  const themeScopeContainer = useThemeScopeContainer();
  const applyMutation = useApplyToShadowJob(job.id);
  const salary = formatSalary(job.salary_min, job.salary_max);
  const postedAgo = job.published_at
    ? formatDistanceToNow(new Date(job.published_at), { addSuffix: true })
    : null;

  const handleConfirmApply = async () => {
    try {
      await applyMutation.mutateAsync();
      setDisclosureOpen(false);
      setApplied(true);
    } catch (err) {
      setDisclosureOpen(false);
      if (err instanceof ApiError && err.status === 400) {
        // Covers both "no Passport yet" and "Passport not approved" -- the backend's own detail
        // message already says which, no need to guess client-side.
        setApplyError(err.detail);
      } else if (err instanceof ApiError && err.status === 409) {
        setApplyError("You've already applied to this role.");
      } else {
        setApplyError("Couldn't submit your application. Try again.");
      }
    }
  };

  if (variant === "compact") {
    return (
      <div className="flex flex-col gap-2">
        <Card className="transition-colors hover:border-muted-foreground/40">
          <CardContent className="flex flex-col gap-3 py-4">
            <div className="flex items-center gap-3">
              <CompanyLogo job={job} size={40} />
              <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                <Link href={`/shadow/jobs/${job.id}`} className="flex items-center gap-1.5">
                  <h3 className="truncate text-sm font-semibold text-foreground">{job.title}</h3>
                  {job.is_verified_employer && (
                    <BadgeCheck className="h-3.5 w-3.5 shrink-0 text-info" />
                  )}
                </Link>
                <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
                  {job.company_slug ? (
                    <Link
                      href={`/shadow/companies/${job.company_slug}`}
                      className="truncate hover:text-brand hover:underline"
                    >
                      {job.company_name}
                    </Link>
                  ) : (
                    <span className="truncate">{job.company_name}</span>
                  )}
                  {job.location && (
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {job.location}
                    </span>
                  )}
                  {salary && <span>{salary}</span>}
                </div>
              </div>
              <MatchScoreRing score={match.match_score} tier={match.match_tier} size={44} strokeWidth={4} />
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                aria-label="Why this matches"
              >
                <ChevronDown className={`h-4 w-4 transition-transform ${expanded ? "rotate-180" : ""}`} />
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="button"
                variant="brand"
                size="sm"
                onClick={saveAction.onToggle}
                disabled={saveAction.pending}
              >
                {saveAction.saved ? (
                  <BookmarkCheck className="h-3.5 w-3.5" />
                ) : (
                  <Bookmark className="h-3.5 w-3.5" />
                )}
                {saveAction.saved ? "Saved" : "Save"}
              </Button>
              <Button
                type="button"
                variant="success"
                size="sm"
                onClick={() => setDisclosureOpen(true)}
                disabled={applied || applyMutation.isPending}
              >
                {applied ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
                {applied ? "Applied" : applyMutation.isPending ? "Applying…" : "Apply"}
              </Button>
              {onDismiss && (
                <Button type="button" variant="danger" size="sm" onClick={onDismiss}>
                  <X className="h-3.5 w-3.5" />
                  Not interested
                </Button>
              )}
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => void shareJob(job.id, job.title, job.company_name)}
              >
                <Share2 className="h-3.5 w-3.5" />
                Share
              </Button>
            </div>

            {applyError && <p className="text-xs font-medium text-danger">{applyError}</p>}
          </CardContent>
        </Card>
        {expanded && (
          <div className="rounded-2xl border border-border bg-card p-4">
            <MatchDetailPanel match={match} />
          </div>
        )}
        <ApplyDisclosureDialog
          open={disclosureOpen}
          onOpenChange={setDisclosureOpen}
          onConfirm={handleConfirmApply}
          isSubmitting={applyMutation.isPending}
          container={themeScopeContainer}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <Card className="border-brand/30 bg-gradient-to-br from-brand/[0.03] to-transparent">
        <CardContent className="flex flex-col gap-4 py-6">
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center rounded-full bg-brand px-2.5 py-0.5 text-xs font-medium text-brand-foreground">
              Top match
            </span>
          </div>

          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex items-start gap-3">
              <CompanyLogo job={job} size={48} />
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-1.5">
                  <Link href={`/shadow/jobs/${job.id}`} className="hover:underline">
                    <h2 className="text-lg font-semibold text-foreground">{job.title}</h2>
                  </Link>
                  {job.is_verified_employer && <BadgeCheck className="h-4 w-4 text-info" />}
                </div>
                {job.company_slug ? (
                  <Link
                    href={`/shadow/companies/${job.company_slug}`}
                    className="w-fit text-sm text-muted-foreground hover:text-brand hover:underline"
                  >
                    {job.company_name}
                  </Link>
                ) : (
                  <p className="text-sm text-muted-foreground">{job.company_name}</p>
                )}
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
                  {job.seniority && <Badge variant="neutral">{job.seniority}</Badge>}
                  {job.remote_preference && (
                    <Badge variant="outline">{REMOTE_PREFERENCE_LABEL[job.remote_preference]}</Badge>
                  )}
                  {postedAgo && <span>Posted {postedAgo}</span>}
                </div>
              </div>
            </div>
            <MatchScoreRing score={match.match_score} tier={match.match_tier} size={72} strokeWidth={6} />
          </div>

          <p className="text-sm text-muted-foreground">{match.summary || job.summary}</p>

          {salary && (
            <p className="text-sm font-medium text-foreground">Salary range: {salary}</p>
          )}

          {match.strengths.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Match highlights
              </p>
              <div className="flex flex-col gap-1">
                {match.strengths.slice(0, MAX_HIGHLIGHTS).map((strength) => (
                  <p key={strength} className="flex items-start gap-1.5 text-sm text-foreground">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />
                    {strength}
                  </p>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-2 border-t border-border pt-4">
            <Button
              type="button"
              variant="brand"
              size="sm"
              onClick={saveAction.onToggle}
              disabled={saveAction.pending}
            >
              {saveAction.saved ? (
                <BookmarkCheck className="h-3.5 w-3.5" />
              ) : (
                <Bookmark className="h-3.5 w-3.5" />
              )}
              {saveAction.saved ? "Saved" : "Save"}
            </Button>
            <Button
              type="button"
              variant="success"
              size="sm"
              onClick={() => setDisclosureOpen(true)}
              disabled={applied || applyMutation.isPending}
            >
              {applied ? (
                <CheckCircle2 className="h-3.5 w-3.5" />
              ) : (
                <Send className="h-3.5 w-3.5" />
              )}
              {applied ? "Applied" : applyMutation.isPending ? "Applying…" : "Apply"}
            </Button>
            {onDismiss && (
              <Button type="button" variant="danger" size="sm" onClick={onDismiss}>
                <X className="h-3.5 w-3.5" />
                Not interested
              </Button>
            )}
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => void shareJob(job.id, job.title, job.company_name)}
            >
              <Share2 className="h-3.5 w-3.5" />
              Share
            </Button>
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="ml-auto flex items-center gap-1 text-xs font-medium text-brand hover:underline"
            >
              Why this matches
              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${expanded ? "rotate-180" : ""}`} />
            </button>
          </div>

          {applyError && <p className="text-xs font-medium text-danger">{applyError}</p>}
        </CardContent>
      </Card>
      {expanded && (
        <div className="rounded-2xl border border-border bg-card p-4">
          <MatchDetailPanel match={match} />
        </div>
      )}
      <ApplyDisclosureDialog
        open={disclosureOpen}
        onOpenChange={setDisclosureOpen}
        onConfirm={handleConfirmApply}
        isSubmitting={applyMutation.isPending}
        container={themeScopeContainer}
      />
    </div>
  );
}
