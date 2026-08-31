import Image from "next/image";
import Link from "next/link";
import { Bookmark, BookmarkCheck, BookmarkX, Briefcase, MapPin } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { API_URL } from "@/lib/api-client";
import { companyAvatar } from "@/lib/company-avatar";
import { formatSalary } from "@/lib/format";
import { EMPLOYMENT_TYPE_LABEL, MATCH_TIER_VARIANT, REMOTE_PREFERENCE_LABEL } from "@/lib/status-display";
import type { ShadowJobBoardListing, ShadowJobMatch } from "@/lib/types";

const MAX_REQUIREMENT_TAGS = 2;

// The one shared job-card renderer for Discover, For You, and Saved Jobs -- previously three
// independently drifting copies of this same markup. Each caller opts into only the pieces it
// needs via props rather than a single rigid "variant" enum, since the three real usages differ
// in more than one dimension at once (For You omits seniority + requirements + the company link
// but keeps the meta row; Saved Jobs omits the whole meta row too).
//
// isNew is additive, opt-in, and defaults off -- Discover/For You/Saved Jobs never pass it and
// render exactly as before. Only Home's "Recommended for you" grid uses it, deriving isNew itself
// from the real job.published_at rather than this component guessing.
//
// The company logo/avatar block always renders (real job.logo_url when a company has uploaded
// one, falling back to a deterministic colored-initial avatar otherwise) -- employers are always
// fully visible on Shadow, so this isn't gated behind an opt-in prop the way isNew is.
export function ShadowJobCard({
  job,
  match,
  description,
  showMeta = true,
  showSeniority = true,
  showRequirements = true,
  showCompanyLink = true,
  isNew = false,
  saveAction,
  unsaveAction,
}: {
  job: ShadowJobBoardListing;
  match?: ShadowJobMatch;
  description?: string;
  showMeta?: boolean;
  showSeniority?: boolean;
  showRequirements?: boolean;
  showCompanyLink?: boolean;
  isNew?: boolean;
  saveAction?: { saved: boolean; onToggle: () => void; pending?: boolean };
  unsaveAction?: { onUnsave: () => void; pending?: boolean };
}) {
  const salary = formatSalary(job.salary_min, job.salary_max);
  const extraRequirements = job.requirements.length - MAX_REQUIREMENT_TAGS;
  const hasCornerAction = !!saveAction || !!unsaveAction;
  const avatar = companyAvatar(job.company_name);

  return (
    <Card className="relative transition-colors hover:border-muted-foreground/40">
      {saveAction && (
        <button
          type="button"
          onClick={saveAction.onToggle}
          disabled={saveAction.pending}
          className="absolute right-4 top-4 z-10 flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          aria-label={saveAction.saved ? "Remove from saved jobs" : "Save this job"}
        >
          {saveAction.saved ? (
            <BookmarkCheck className="h-4 w-4 text-brand" />
          ) : (
            <Bookmark className="h-4 w-4" />
          )}
        </button>
      )}
      {unsaveAction && (
        <button
          type="button"
          onClick={unsaveAction.onUnsave}
          disabled={unsaveAction.pending}
          className="absolute right-4 top-4 z-10 flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-danger"
          aria-label="Remove from saved jobs"
        >
          <BookmarkX className="h-4 w-4" />
        </button>
      )}

      <CardContent className="flex flex-col gap-2.5 py-5">
        <Link
          href={`/shadow/jobs/${job.id}`}
          className={`flex flex-col gap-2.5 ${hasCornerAction ? "pr-8" : ""}`}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-2.5">
              {job.logo_url ? (
                <div className="relative h-9 w-9 shrink-0 overflow-hidden rounded-lg border border-border bg-card">
                  <Image
                    src={`${API_URL}${job.logo_url}`}
                    alt=""
                    fill
                    className="object-contain"
                    unoptimized
                  />
                </div>
              ) : (
                <div
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-semibold ${avatar.colorClassName}`}
                >
                  {avatar.initial}
                </div>
              )}
              <div className="flex flex-col gap-0.5">
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-semibold text-foreground">{job.title}</h2>
                  {isNew && <Badge variant="info">New</Badge>}
                </div>
                <p className="text-sm text-muted-foreground">{job.company_name}</p>
              </div>
            </div>
            <div className="flex shrink-0 flex-col items-end gap-1.5">
              {match && (
                <>
                  <Badge variant={MATCH_TIER_VARIANT[match.match_tier]}>{match.match_tier}</Badge>
                  <span className="text-xs font-medium text-muted-foreground">
                    {match.match_score}% match
                  </span>
                </>
              )}
              {salary && <Badge variant="success">{salary}</Badge>}
            </div>
          </div>

          <p className="line-clamp-2 text-sm text-muted-foreground">
            {description ?? job.summary}
          </p>

          {showMeta && (
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
              {showSeniority && job.seniority && <Badge variant="neutral">{job.seniority}</Badge>}
            </div>
          )}

          {showRequirements && job.requirements.length > 0 && (
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
                <span className="text-[11px] text-muted-foreground">+{extraRequirements} more</span>
              )}
            </div>
          )}
        </Link>

        {showCompanyLink && job.company_slug && (
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
}
