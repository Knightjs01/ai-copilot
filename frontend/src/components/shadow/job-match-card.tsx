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
  Share2,
  X,
} from "lucide-react";

import { MatchDetailPanel } from "@/components/shadow/match-detail-panel";
import { MatchScoreRing } from "@/components/shadow/match-score-ring";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { API_URL } from "@/lib/api-client";
import { companyAvatar } from "@/lib/company-avatar";
import { formatSalary } from "@/lib/format";
import { EMPLOYMENT_TYPE_LABEL, REMOTE_PREFERENCE_LABEL } from "@/lib/status-display";
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
  const salary = formatSalary(job.salary_min, job.salary_max);
  const postedAgo = job.published_at
    ? formatDistanceToNow(new Date(job.published_at), { addSuffix: true })
    : null;

  if (variant === "compact") {
    return (
      <div className="flex flex-col gap-2">
        <Card className="transition-colors hover:border-muted-foreground/40">
          <CardContent className="flex items-center gap-3 py-4">
            <CompanyLogo job={job} size={40} />
            <Link href={`/shadow/jobs/${job.id}`} className="flex min-w-0 flex-1 flex-col gap-0.5">
              <div className="flex items-center gap-1.5">
                <h3 className="truncate text-sm font-semibold text-foreground">{job.title}</h3>
                {job.is_verified_employer && (
                  <BadgeCheck className="h-3.5 w-3.5 shrink-0 text-info" />
                )}
              </div>
              <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
                <span className="truncate">{job.company_name}</span>
                {job.location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    {job.location}
                  </span>
                )}
                {salary && <span>{salary}</span>}
              </div>
            </Link>
            <MatchScoreRing score={match.match_score} tier={match.match_tier} size={44} strokeWidth={4} />
            <button
              type="button"
              onClick={saveAction.onToggle}
              disabled={saveAction.pending}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              aria-label={saveAction.saved ? "Remove from saved jobs" : "Save this job"}
            >
              {saveAction.saved ? (
                <BookmarkCheck className="h-4 w-4 text-brand" />
              ) : (
                <Bookmark className="h-4 w-4" />
              )}
            </button>
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              aria-label="Why this matches"
            >
              <ChevronDown className={`h-4 w-4 transition-transform ${expanded ? "rotate-180" : ""}`} />
            </button>
          </CardContent>
        </Card>
        {expanded && (
          <div className="rounded-2xl border border-border bg-card p-4">
            <MatchDetailPanel match={match} />
          </div>
        )}
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
                <p className="text-sm text-muted-foreground">{job.company_name}</p>
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
            <button
              type="button"
              onClick={saveAction.onToggle}
              disabled={saveAction.pending}
              className="flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary"
            >
              {saveAction.saved ? (
                <BookmarkCheck className="h-3.5 w-3.5 text-brand" />
              ) : (
                <Bookmark className="h-3.5 w-3.5" />
              )}
              {saveAction.saved ? "Saved" : "Save"}
            </button>
            <button
              type="button"
              onClick={() => void shareJob(job.id, job.title, job.company_name)}
              className="flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary"
            >
              <Share2 className="h-3.5 w-3.5" />
              Share
            </button>
            {onDismiss && (
              <button
                type="button"
                onClick={onDismiss}
                className="flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-secondary"
              >
                <X className="h-3.5 w-3.5" />
                Not interested
              </button>
            )}
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="ml-auto flex items-center gap-1 text-xs font-medium text-brand hover:underline"
            >
              Why this matches
              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${expanded ? "rotate-180" : ""}`} />
            </button>
          </div>
        </CardContent>
      </Card>
      {expanded && (
        <div className="rounded-2xl border border-border bg-card p-4">
          <MatchDetailPanel match={match} />
        </div>
      )}
    </div>
  );
}
