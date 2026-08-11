"use client";

import { Eye } from "lucide-react";

import { RequestRevealDialog } from "@/components/shadow-jobs/request-reveal-dialog";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useRevealedIdentity } from "@/lib/queries/shadow-reveal";
import { SHADOW_APPLICATION_STATUS_LABEL, SHADOW_APPLICATION_STATUS_VARIANT } from "@/lib/status-display";
import type { ShadowProfile } from "@/lib/types";

export function ApplicantCard({ jobId, profile }: { jobId: string; profile: ShadowProfile }) {
  const isRevealable = profile.status === "revealed";
  const { data: identity } = useRevealedIdentity(
    jobId,
    isRevealable ? profile.application_id : undefined
  );

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-0.5">
            <h3 className="text-base font-semibold text-foreground">{profile.callsign}</h3>
            {profile.headline && (
              <p className="text-sm text-muted-foreground">{profile.headline}</p>
            )}
          </div>
          <Badge variant={SHADOW_APPLICATION_STATUS_VARIANT[profile.status]}>
            {SHADOW_APPLICATION_STATUS_LABEL[profile.status]}
          </Badge>
        </div>

        {profile.summary && <p className="text-sm text-foreground">{profile.summary}</p>}

        {profile.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {profile.skills.map((skill) => (
              <Badge key={skill} variant="outline">
                {skill}
              </Badge>
            ))}
          </div>
        )}

        {profile.career_entries.length > 0 && (
          <div className="flex flex-col gap-1 text-sm text-muted-foreground">
            {profile.career_entries.map((entry, i) => (
              <p key={i}>
                {entry.title} · {entry.company_name_anonymized}
                {entry.is_current ? " (current)" : ""}
              </p>
            ))}
          </div>
        )}

        {identity ? (
          <div className="flex flex-col gap-1 rounded-xl border border-success/30 bg-success/5 p-3">
            <div className="flex items-center gap-1.5 text-sm font-medium text-success">
              <Eye className="h-3.5 w-3.5" />
              Identity revealed
            </div>
            <p className="text-sm text-foreground">{identity.full_name}</p>
            <p className="text-sm text-muted-foreground">{identity.email}</p>
            {identity.phone && <p className="text-sm text-muted-foreground">{identity.phone}</p>}
            {identity.career_entries.map((entry, i) => (
              <p key={i} className="text-xs text-muted-foreground">
                {entry.title} · {entry.company_name}
                {entry.is_current ? " (current)" : ""}
              </p>
            ))}
          </div>
        ) : (
          <div className="flex justify-end">
            {profile.status === "submitted" || profile.status === "under_review" ? (
              <RequestRevealDialog
                jobId={jobId}
                applicationId={profile.application_id}
                callsign={profile.callsign}
              />
            ) : profile.status === "reveal_requested" ? (
              <p className="text-xs text-muted-foreground">
                Waiting on {profile.callsign} to respond to your reveal request.
              </p>
            ) : profile.status === "declined" ? (
              <p className="text-xs text-muted-foreground">
                {profile.callsign} declined this reveal request.
              </p>
            ) : null}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
