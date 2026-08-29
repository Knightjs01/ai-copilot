"use client";

import * as React from "react";

import { ProfileSubmittedOverlay } from "@/components/company/profile-submitted-overlay";
import { PublishChangesDialog } from "@/components/company/publish-changes-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  usePauseProfile,
  useResumeProfile,
  useSubmitForReview,
} from "@/lib/queries/company";
import { COMPANY_PROFILE_STATUS_LABEL, COMPANY_PROFILE_STATUS_VARIANT } from "@/lib/status-display";
import { useToast } from "@/lib/toast-context";
import type { CompanyProfileStatus } from "@/lib/types";

export function CompanyStatusStrip({ status }: { status: CompanyProfileStatus }) {
  const submitForReview = useSubmitForReview();
  const pause = usePauseProfile();
  const resume = useResumeProfile();
  const toast = useToast();
  const [showSubmittedOverlay, setShowSubmittedOverlay] = React.useState(false);

  const handleSubmit = () => {
    submitForReview.mutate(undefined, {
      onSuccess: () => setShowSubmittedOverlay(true),
      onError: () => toast({ title: "Couldn't submit for review", variant: "danger" }),
    });
  };
  const handlePause = () => {
    pause.mutate(undefined, {
      onSuccess: () => toast({ title: "Profile paused", variant: "success" }),
      onError: () => toast({ title: "Couldn't pause", variant: "danger" }),
    });
  };
  const handleResume = () => {
    resume.mutate(undefined, {
      onSuccess: () => toast({ title: "Profile resumed", variant: "success" }),
      onError: () => toast({ title: "Couldn't resume", variant: "danger" }),
    });
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-card px-5 py-4">
      <div className="flex items-center gap-3">
        <Badge variant={COMPANY_PROFILE_STATUS_VARIANT[status]}>
          {COMPANY_PROFILE_STATUS_LABEL[status]}
        </Badge>
        <p className="text-sm text-muted-foreground">
          {status === "draft" && "Not visible to candidates yet."}
          {status === "pending_review" && "Phantom is reviewing your submission."}
          {status === "live" && "Visible on your public profile page."}
          {status === "paused" && "Hidden from candidates until you resume."}
          {status === "suspended" && "Hidden by Phantom staff — contact support."}
        </p>
      </div>
      <div className="flex gap-2">
        {status === "draft" && (
          <Button
            type="button"
            variant="brand"
            size="sm"
            onClick={handleSubmit}
            disabled={submitForReview.isPending}
          >
            {submitForReview.isPending ? "Submitting…" : "Submit for review"}
          </Button>
        )}
        {(status === "live" || status === "paused") && <PublishChangesDialog />}
        {status === "live" && (
          <Button type="button" variant="secondary" size="sm" onClick={handlePause} disabled={pause.isPending}>
            {pause.isPending ? "Pausing…" : "Pause"}
          </Button>
        )}
        {status === "paused" && (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleResume}
            disabled={resume.isPending}
          >
            {resume.isPending ? "Resuming…" : "Resume"}
          </Button>
        )}
      </div>
      <ProfileSubmittedOverlay
        active={showSubmittedOverlay}
        onDismiss={() => setShowSubmittedOverlay(false)}
      />
    </div>
  );
}
