"use client";

import * as React from "react";
import { format } from "date-fns";
import { Calendar, CheckCircle2, XCircle } from "lucide-react";

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
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { InterviewScorecardDialog } from "@/components/shadow-jobs/interview-scorecard-dialog";
import { useAuth } from "@/lib/auth-context";
import { useTeam } from "@/lib/queries/team";
import {
  useApplicantInterviews,
  useCancelInterview,
  useCompleteInterview,
  useScheduleInterview,
} from "@/lib/queries/shadow-jobs";
import { INTERVIEW_STATUS_LABEL, INTERVIEW_STATUS_VARIANT } from "@/lib/status-display";
import { useToast } from "@/lib/toast-context";
import type { Interview, UserRead } from "@/lib/types";

export function InterviewRow({
  interview,
  jobId,
  applicationId,
  canSchedule,
  team,
}: {
  interview: Interview;
  jobId: string;
  applicationId: string;
  canSchedule: boolean;
  team: UserRead[] | undefined;
}) {
  const { user, hasPermission } = useAuth();
  const canScoreInterview =
    hasPermission("interviews.schedule") ||
    (!!user && interview.interviewer_user_ids.includes(user.id));
  const cancelInterview = useCancelInterview(jobId, applicationId, interview.id);
  const completeInterview = useCompleteInterview(jobId, applicationId, interview.id);
  const toast = useToast();
  const interviewerNames = (team ?? [])
    .filter((member) => interview.interviewer_user_ids.includes(member.id))
    .map((member) => member.full_name);

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
    <div className="flex items-center justify-between gap-3 rounded-xl border border-border p-3">
      <div className="flex flex-col gap-0.5">
        <p className="text-sm font-medium text-foreground">
          {format(new Date(interview.scheduled_at), "d MMM yyyy, h:mm a")}
        </p>
        {interview.location && (
          <p className="text-xs text-muted-foreground">{interview.location}</p>
        )}
        {interview.meeting_link && (
          <a
            href={interview.meeting_link}
            target="_blank"
            rel="noreferrer"
            className="text-xs text-brand underline underline-offset-2"
          >
            {interview.meeting_link}
          </a>
        )}
        {interviewerNames.length > 0 && (
          <p className="text-xs text-muted-foreground">
            Interviewer{interviewerNames.length > 1 ? "s" : ""}: {interviewerNames.join(", ")}
          </p>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Badge variant={INTERVIEW_STATUS_VARIANT[interview.status]}>
          {INTERVIEW_STATUS_LABEL[interview.status]}
        </Badge>
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
              className="flex h-7 w-7 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-success"
              aria-label="Mark complete"
            >
              <CheckCircle2 className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={handleCancel}
              disabled={cancelInterview.isPending}
              className="flex h-7 w-7 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-danger"
              aria-label="Cancel interview"
            >
              <XCircle className="h-4 w-4" />
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export function ScheduleInterviewDialog({
  jobId,
  applicationId,
  callsign,
  displayName,
}: {
  jobId: string;
  applicationId: string;
  callsign: string;
  // Once identity is revealed, interview workflows should read like they're about a real person
  // -- falls back to the Callsign when not yet revealed.
  displayName?: string;
}) {
  const { hasPermission } = useAuth();
  const canSchedule = hasPermission("interviews.schedule");
  const [open, setOpen] = React.useState(false);
  const [scheduledAt, setScheduledAt] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [meetingLink, setMeetingLink] = React.useState("");
  const [interviewerIds, setInterviewerIds] = React.useState<string[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  const { data: team } = useTeam();
  const { data: interviews, isLoading } = useApplicantInterviews(
    open ? jobId : undefined,
    open ? applicationId : undefined
  );
  const scheduleInterview = useScheduleInterview(jobId, applicationId);

  const toggleInterviewer = (userId: string) => {
    setInterviewerIds((current) =>
      current.includes(userId)
        ? current.filter((id) => id !== userId)
        : [...current, userId]
    );
  };

  const handleSchedule = async () => {
    if (!scheduledAt) return;
    setError(null);
    try {
      await scheduleInterview.mutateAsync({
        scheduled_at: new Date(scheduledAt).toISOString(),
        location: location || undefined,
        meeting_link: meetingLink || undefined,
        interviewer_user_ids: interviewerIds,
      });
      setScheduledAt("");
      setLocation("");
      setMeetingLink("");
      setInterviewerIds([]);
    } catch {
      setError("Couldn't schedule interview. Check the date is in the future and try again.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="secondary" size="sm">
          <Calendar className="h-3.5 w-3.5" />
          Interview
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Interviews with {displayName ?? callsign}</DialogTitle>
          <DialogDescription>
            Schedule, reschedule, or cancel interviews for this applicant.
          </DialogDescription>
        </DialogHeader>

        {!isLoading && interviews && interviews.length > 0 && (
          <div className="flex flex-col gap-2">
            {interviews.map((interview) => (
              <InterviewRow
                key={interview.id}
                interview={interview}
                jobId={jobId}
                applicationId={applicationId}
                canSchedule={canSchedule}
                team={team}
              />
            ))}
          </div>
        )}

        {canSchedule && (
          <div className="flex flex-col gap-3 border-t border-border pt-4">
            <Field label="Date & time" htmlFor="scheduledAt">
              <Input
                id="scheduledAt"
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
              />
            </Field>
            <Field label="Location (optional)" htmlFor="location">
              <Input
                id="location"
                placeholder="e.g. Zoom, or office address"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </Field>
            <Field label="Meeting link (optional)" htmlFor="meetingLink">
              <Input
                id="meetingLink"
                placeholder="https://…"
                value={meetingLink}
                onChange={(e) => setMeetingLink(e.target.value)}
              />
            </Field>
            {team && team.length > 0 && (
              <Field label="Interviewer(s) (optional)">
                <div className="flex flex-col gap-1.5">
                  {team.map((member) => (
                    <label
                      key={member.id}
                      className="flex items-center gap-2 text-sm text-foreground"
                    >
                      <input
                        type="checkbox"
                        checked={interviewerIds.includes(member.id)}
                        onChange={() => toggleInterviewer(member.id)}
                        className="accent-brand"
                      />
                      {member.full_name}
                    </label>
                  ))}
                </div>
              </Field>
            )}
            {error && <p className="text-sm font-medium text-danger">{error}</p>}
            <div className="flex justify-end">
              <Button
                type="button"
                variant="brand"
                onClick={handleSchedule}
                disabled={!scheduledAt || scheduleInterview.isPending}
              >
                {scheduleInterview.isPending ? "Scheduling…" : "Schedule interview"}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
