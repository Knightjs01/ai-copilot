"use client";

import * as React from "react";
import Link from "next/link";
import { Eye, MessageCircle } from "lucide-react";

import { RequestRevealDialog } from "@/components/shadow-jobs/request-reveal-dialog";
import { SaveToTalentPoolDialog } from "@/components/shadow-jobs/save-to-talent-pool-dialog";
import { ScheduleInterviewDialog } from "@/components/shadow-jobs/schedule-interview-dialog";
import { StepUpDialog } from "@/components/step-up-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";
import { useMarkApplicantViewed } from "@/lib/queries/shadow-jobs";
import { useFetchRevealedIdentity } from "@/lib/queries/shadow-reveal";
import { cn } from "@/lib/utils";
import {
  SHADOW_APPLICATION_STATUS_LABEL,
  SHADOW_APPLICATION_STATUS_VARIANT,
  SHADOW_EFFECTIVE_STAGE_LABEL,
  SHADOW_EFFECTIVE_STAGE_VARIANT,
  TALENT_POOL_STATUS_LABEL,
  TALENT_POOL_STATUS_VARIANT,
} from "@/lib/status-display";
import type { RevealedIdentity, ShadowJobStatus, ShadowProfile } from "@/lib/types";

export function ApplicantCard({
  jobId,
  jobStatus,
  profile,
}: {
  jobId: string;
  jobStatus: ShadowJobStatus;
  profile: ShadowProfile;
}) {
  const { hasPermission } = useAuth();
  const isRevealable = profile.status === "revealed";
  const [identity, setIdentity] = React.useState<RevealedIdentity | null>(null);
  const [stepUpOpen, setStepUpOpen] = React.useState(false);
  const fetchIdentity = useFetchRevealedIdentity(jobId);
  const markViewed = useMarkApplicantViewed(jobId);
  const markViewedRef = React.useRef(markViewed.mutate);
  markViewedRef.current = markViewed.mutate;

  // Opening this list is a real "the recruiter looked at their applicants" signal -- each card
  // clears its own "new" flag once it's actually rendered here, not just when the list loads.
  // Covers both a brand-new application and an unseen reveal-request response.
  React.useEffect(() => {
    if (profile.is_new || profile.reveal_response_is_new) {
      markViewedRef.current(profile.application_id);
    }
  }, [profile.is_new, profile.reveal_response_is_new, profile.application_id]);
  const canRequestTalentPool =
    hasPermission("talent_pool.request") &&
    (jobStatus === "closed" || profile.status === "declined" || profile.status === "withdrawn");
  const talentPoolActionable =
    canRequestTalentPool &&
    (profile.talent_pool_status === null ||
      profile.talent_pool_status === "declined" ||
      profile.talent_pool_status === "withdrawn");

  const handleVerified = async (stepUpToken: string) => {
    const result = await fetchIdentity.mutateAsync({
      applicationId: profile.application_id,
      stepUpToken,
    });
    setIdentity(result);
  };

  return (
    <Card
      className={cn((profile.is_new || profile.reveal_response_is_new) && "border-brand/50 bg-brand/5")}
    >
      <CardContent className="flex flex-col gap-3 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-0.5">
            <h3 className="flex items-center gap-1.5 text-base font-semibold text-foreground">
              <Link
                href={`/shadow-jobs/${jobId}/applicants/${profile.application_id}`}
                className="hover:underline"
              >
                {profile.callsign}
              </Link>
              {profile.is_new && <Badge variant="success">New application</Badge>}
              {profile.reveal_response_is_new && <Badge variant="info">Reveal response</Badge>}
            </h3>
            {profile.headline && (
              <p className="text-sm text-muted-foreground">{profile.headline}</p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            <Badge variant={SHADOW_EFFECTIVE_STAGE_VARIANT[profile.effective_stage]}>
              {SHADOW_EFFECTIVE_STAGE_LABEL[profile.effective_stage]}
            </Badge>
            {profile.effective_stage !== "withdrawn" && (
              <Badge variant={SHADOW_APPLICATION_STATUS_VARIANT[profile.status]}>
                {SHADOW_APPLICATION_STATUS_LABEL[profile.status]}
              </Badge>
            )}
          </div>
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
            {identity.full_name && (
              <p className="text-sm text-foreground">{identity.full_name}</p>
            )}
            {identity.email && <p className="text-sm text-muted-foreground">{identity.email}</p>}
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
            {isRevealable ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setStepUpOpen(true)}
                disabled={fetchIdentity.isPending}
              >
                <Eye className="h-3.5 w-3.5" />
                {fetchIdentity.isPending ? "Verifying…" : "View revealed identity"}
              </Button>
            ) : profile.status === "submitted" || profile.status === "under_review" ? (
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

        {canRequestTalentPool && (
          <div className="flex items-center justify-end gap-2 border-t border-border pt-3">
            {talentPoolActionable ? (
              <SaveToTalentPoolDialog
                jobId={jobId}
                applicationId={profile.application_id}
                callsign={profile.callsign}
              />
            ) : profile.talent_pool_status === "requested" ? (
              <p className="text-xs text-muted-foreground">
                Waiting on {profile.callsign} to respond to your Talent Pool request.
              </p>
            ) : profile.talent_pool_status === "granted" ? (
              <Badge variant={TALENT_POOL_STATUS_VARIANT.granted}>
                {TALENT_POOL_STATUS_LABEL.granted}
              </Badge>
            ) : null}
          </div>
        )}

        {(hasPermission("messages.view") || hasPermission("interviews.view")) && (
          <div className="flex justify-end gap-2 border-t border-border pt-3">
            {hasPermission("interviews.view") && (
              <div className="flex items-center gap-1.5">
                {profile.has_upcoming_interview && <Badge variant="info">Upcoming</Badge>}
                <ScheduleInterviewDialog
                  jobId={jobId}
                  applicationId={profile.application_id}
                  callsign={profile.callsign}
                />
              </div>
            )}
            {hasPermission("messages.view") && (
              <Button variant="secondary" size="sm" asChild>
                <Link href={`/shadow-jobs/${jobId}/applicants/${profile.application_id}/messages`}>
                  <MessageCircle className="h-3.5 w-3.5" />
                  Message
                  {profile.unread_message_count > 0 && (
                    <Badge variant="info" className="ml-1">
                      {profile.unread_message_count}
                    </Badge>
                  )}
                </Link>
              </Button>
            )}
          </div>
        )}
      </CardContent>
      <StepUpDialog
        open={stepUpOpen}
        onOpenChange={setStepUpOpen}
        title="Confirm it's you"
        description="Viewing a revealed identity is a high-risk action — re-enter your password to continue."
        onVerified={handleVerified}
      />
    </Card>
  );
}
