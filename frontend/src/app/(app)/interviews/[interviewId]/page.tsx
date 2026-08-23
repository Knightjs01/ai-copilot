"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { format } from "date-fns";
import { ArrowLeft, Calendar, CheckCircle2, MapPin, ShieldAlert, Video, XCircle } from "lucide-react";

import { InterviewScorecardDialog } from "@/components/shadow-jobs/interview-scorecard-dialog";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";
import { useCancelInterview, useCompanyInterviews, useCompleteInterview } from "@/lib/queries/shadow-jobs";
import { INTERVIEW_STATUS_LABEL, INTERVIEW_STATUS_VARIANT } from "@/lib/status-display";
import { useToast } from "@/lib/toast-context";

// A minimal, standalone interview detail page reachable by anyone holding just interviews.view --
// unlike the applicant workspace page (gated on shadow_jobs.view) or a project's own Interviews
// tab (gated on projects.view), this page exists specifically so a participant Interviewer (who
// holds neither of those) has somewhere real to land and act on an interview they're assigned to.
export default function InterviewDetailPage() {
  const { interviewId } = useParams<{ interviewId: string }>();
  const { user, hasPermission } = useAuth();
  const toast = useToast();
  const canView = hasPermission("interviews.view");
  const canSchedule = hasPermission("interviews.schedule");

  const { data: interviews, isLoading } = useCompanyInterviews({ enabled: canView });
  const interview = interviews?.find((i) => i.id === interviewId);

  const jobId = interview?.shadow_job_id ?? "";
  const applicationId = interview?.application_id ?? "";
  const cancelInterview = useCancelInterview(jobId, applicationId, interviewId);
  const completeInterview = useCompleteInterview(jobId, applicationId, interviewId);

  const canScoreInterview =
    canSchedule || (!!user && !!interview?.interviewer_user_ids.includes(user.id));

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Interviews aren&apos;t available on your role</p>
      </div>
    );
  }

  if (isLoading) {
    return <Spinner className="h-5 w-5 text-muted-foreground" />;
  }

  if (!interview) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <Calendar className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Interview not found</p>
        <p className="text-sm text-muted-foreground">
          It may have been cancelled, or you&apos;re not assigned to it.
        </p>
        <Link href="/interviews" className="text-sm font-medium text-brand hover:underline">
          Back to Interviews
        </Link>
      </div>
    );
  }

  const handleCancel = () => {
    cancelInterview.mutate(undefined, {
      onSuccess: () => toast({ title: "Interview cancelled", variant: "success" }),
      onError: () => toast({ title: "Couldn't cancel interview", variant: "danger" }),
    });
  };

  const handleComplete = () => {
    completeInterview.mutate(undefined, {
      onSuccess: () => toast({ title: "Interview marked complete", variant: "success" }),
      onError: () => toast({ title: "Couldn't update interview", variant: "danger" }),
    });
  };

  return (
    <div className="flex flex-col gap-6">
      <Link
        href="/interviews"
        className="flex w-fit items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Interviews
      </Link>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Video className="h-5 w-5 text-brand" />
              {interview.job_title}
            </CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">{interview.callsign}</p>
          </div>
          <Badge variant={INTERVIEW_STATUS_VARIANT[interview.status]}>
            {INTERVIEW_STATUS_LABEL[interview.status]}
          </Badge>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5 text-sm text-foreground">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 shrink-0 text-muted-foreground" />
              {format(new Date(interview.scheduled_at), "EEEE d MMMM yyyy, HH:mm")}
            </div>
            {interview.location && (
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 shrink-0 text-muted-foreground" />
                {interview.location}
              </div>
            )}
            {interview.meeting_link && (
              <a
                href={interview.meeting_link}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 text-brand underline underline-offset-2"
              >
                <Video className="h-4 w-4 shrink-0" />
                {interview.meeting_link}
              </a>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2 border-t border-border pt-4">
            {canScoreInterview && (
              <InterviewScorecardDialog
                jobId={jobId}
                applicationId={applicationId}
                interviewId={interview.id}
              />
            )}
            {canSchedule && interview.status === "scheduled" && (
              <>
                <button
                  type="button"
                  onClick={handleComplete}
                  disabled={completeInterview.isPending}
                  className="flex h-8 items-center gap-1.5 rounded-full border border-border px-3 text-sm text-muted-foreground transition-colors hover:border-success/40 hover:text-success"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Mark complete
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  disabled={cancelInterview.isPending}
                  className="flex h-8 items-center gap-1.5 rounded-full border border-border px-3 text-sm text-muted-foreground transition-colors hover:border-danger/40 hover:text-danger"
                >
                  <XCircle className="h-3.5 w-3.5" />
                  Cancel interview
                </button>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
