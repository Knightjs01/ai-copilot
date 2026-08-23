"use client";

import { FileText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { NOTICE_PERIOD_LABEL, REMOTE_PREFERENCE_LABEL } from "@/lib/status-display";
import type { RevealedIdentity, ShadowProfile } from "@/lib/types";

function formatSalary(min: number | null, max: number | null): string | null {
  if (min == null && max == null) return null;
  const fmt = (n: number) => `£${n.toLocaleString()}`;
  if (min != null && max != null) return `${fmt(min)} – ${fmt(max)}`;
  return fmt((min ?? max) as number);
}

// Read-only, company-facing sibling of the candidate's own anonymised-cv-dialog.tsx -- same
// "exactly what a company sees" promise, but no Approve/Decline actions (nothing to review here,
// this already IS what was submitted). Upgrades to the real, revealed name and employer names
// once `identity` is passed in -- only ever set this session after the recruiter has completed
// step-up and actually fetched RevealedIdentity, never just because the application is eligible
// (see PassportCard's own revealedName prop for the identical discipline).
export function AnonymizedCvDialog({
  profile,
  identity,
}: {
  profile: ShadowProfile;
  identity?: RevealedIdentity | null;
}) {
  const isRevealed = identity != null;

  const factsLine = [
    profile.seniority,
    profile.location,
    profile.remote_preference ? REMOTE_PREFERENCE_LABEL[profile.remote_preference] : null,
    formatSalary(profile.salary_min, profile.salary_max),
    profile.notice_period ? `${NOTICE_PERIOD_LABEL[profile.notice_period]} notice` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const careerEntries = isRevealed
    ? identity.career_entries.map((entry) => ({
        title: entry.title,
        company: entry.company_name,
        isCurrent: entry.is_current,
      }))
    : profile.career_entries.map((entry) => ({
        title: entry.title,
        company: entry.company_name_anonymized,
        isCurrent: entry.is_current,
      }));

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button type="button" variant="secondary" size="sm">
          <FileText className="h-3.5 w-3.5" />
          {isRevealed ? "View CV" : "View anonymised CV"}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {isRevealed ? `${identity.full_name}'s CV` : `${profile.callsign}'s anonymised CV`}
          </DialogTitle>
          <DialogDescription>
            {isRevealed
              ? "This candidate approved your Reveal Request — real name and employer names below."
              : "Exactly what this candidate submitted — no name or real employer, until they approve a Reveal Request."}
          </DialogDescription>
        </DialogHeader>

        <div className="flex max-h-[65vh] flex-col gap-5 overflow-y-auto rounded-xl border border-border bg-background p-5">
          <div className="flex flex-col gap-1">
            <p className="text-lg font-semibold text-foreground">
              {profile.headline || "Untitled role"}
            </p>
            {factsLine && <p className="text-sm text-muted-foreground">{factsLine}</p>}
            {isRevealed && (identity.email || identity.phone) && (
              <p className="text-sm text-muted-foreground">
                {[identity.email, identity.phone].filter(Boolean).join(" · ")}
              </p>
            )}
          </div>

          {profile.summary && <p className="text-sm text-foreground">{profile.summary}</p>}

          {profile.skills.length > 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Skills
              </p>
              <div className="flex flex-wrap gap-1.5">
                {profile.skills.map((skill) => (
                  <Badge key={skill} variant="neutral">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {profile.industries.length > 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Industries
              </p>
              <div className="flex flex-wrap gap-1.5">
                {profile.industries.map((industry) => (
                  <Badge key={industry} variant="neutral">
                    {industry}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-col gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Career history
            </p>
            {careerEntries.length > 0 ? (
              <div className="flex flex-col gap-2">
                {careerEntries.map((entry, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between gap-2 rounded-lg bg-card p-3"
                  >
                    <p className="text-sm font-medium text-foreground">{entry.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {entry.company}
                      {entry.isCurrent && (
                        <Badge variant="success" className="ml-1.5">
                          Current
                        </Badge>
                      )}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No career history on this application.</p>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
