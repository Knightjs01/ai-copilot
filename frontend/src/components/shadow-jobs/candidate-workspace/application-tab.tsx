import { format } from "date-fns";

import { Badge } from "@/components/ui/badge";
import {
  SHADOW_APPLICATION_STATUS_LABEL,
  SHADOW_APPLICATION_STATUS_VARIANT,
  SHADOW_EFFECTIVE_STAGE_LABEL,
  SHADOW_EFFECTIVE_STAGE_VARIANT,
} from "@/lib/status-display";
import type { RevealedIdentity, ShadowProfile } from "@/lib/types";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <div className="text-sm text-foreground">{children}</div>
    </div>
  );
}

export function ApplicationTab({
  jobTitle,
  profile,
  identity,
}: {
  jobTitle: string;
  profile: ShadowProfile;
  identity?: RevealedIdentity | null;
}) {
  const isRevealed = identity != null;
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
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Candidate">{isRevealed ? identity.full_name : profile.callsign}</Field>
        <Field label="Role applied for">{jobTitle}</Field>
        <Field label="Date applied">{format(new Date(profile.applied_at), "d MMM yyyy")}</Field>
        <Field label="Current stage">
          <Badge variant={SHADOW_EFFECTIVE_STAGE_VARIANT[profile.effective_stage]}>
            {SHADOW_EFFECTIVE_STAGE_LABEL[profile.effective_stage]}
          </Badge>
        </Field>
        <Field label="Source">Shadow</Field>
        <Field label="Application status">
          <Badge variant={SHADOW_APPLICATION_STATUS_VARIANT[profile.status]}>
            {SHADOW_APPLICATION_STATUS_LABEL[profile.status]}
          </Badge>
        </Field>
      </div>

      {profile.summary && (
        <div className="flex flex-col gap-1.5">
          <h3 className="text-sm font-medium text-foreground">Candidate summary</h3>
          <p className="text-sm text-foreground">{profile.summary}</p>
        </div>
      )}

      {profile.skills.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <h3 className="text-sm font-medium text-foreground">Relevant skills</h3>
          <div className="flex flex-wrap gap-1.5">
            {profile.skills.map((skill) => (
              <Badge key={skill} variant="neutral">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {careerEntries.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <h3 className="text-sm font-medium text-foreground">Relevant career history</h3>
          <div className="flex flex-col gap-1 text-sm text-muted-foreground">
            {careerEntries.map((entry, i) => (
              <p key={i}>
                {entry.title} · {entry.company}
                {entry.isCurrent ? " (current)" : ""}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
