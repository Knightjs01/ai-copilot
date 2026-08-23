"use client";

import * as React from "react";

import { InterviewRow } from "@/components/shadow-jobs/schedule-interview-dialog";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";
import { useTeam } from "@/lib/queries/team";
import { useApplicantInterviews, useScheduleInterview } from "@/lib/queries/shadow-jobs";

export function InterviewsTab({
  jobId,
  applicationId,
}: {
  jobId: string;
  applicationId: string;
}) {
  const { hasPermission } = useAuth();
  const canSchedule = hasPermission("interviews.schedule");
  const { data: team } = useTeam();
  const { data: interviews, isLoading } = useApplicantInterviews(jobId, applicationId);
  const scheduleInterview = useScheduleInterview(jobId, applicationId);

  const [scheduledAt, setScheduledAt] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [meetingLink, setMeetingLink] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);

  const handleSchedule = async () => {
    if (!scheduledAt) return;
    setError(null);
    try {
      await scheduleInterview.mutateAsync({
        scheduled_at: new Date(scheduledAt).toISOString(),
        location: location || undefined,
        meeting_link: meetingLink || undefined,
        interviewer_user_ids: [],
      });
      setScheduledAt("");
      setLocation("");
      setMeetingLink("");
    } catch {
      setError("Couldn't schedule interview. Check the date is in the future and try again.");
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {interviews && interviews.length > 0 ? (
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
      ) : (
        <p className="text-sm text-muted-foreground">No interviews scheduled yet.</p>
      )}

      {canSchedule && (
        <div className="flex flex-col gap-3 border-t border-border pt-5">
          <h3 className="text-sm font-medium text-foreground">Schedule an interview</h3>
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Date & time" htmlFor="workspaceScheduledAt">
              <Input
                id="workspaceScheduledAt"
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
              />
            </Field>
            <Field label="Location (optional)" htmlFor="workspaceLocation">
              <Input
                id="workspaceLocation"
                placeholder="e.g. Zoom, or office address"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </Field>
            <Field label="Meeting link (optional)" htmlFor="workspaceMeetingLink">
              <Input
                id="workspaceMeetingLink"
                placeholder="https://…"
                value={meetingLink}
                onChange={(e) => setMeetingLink(e.target.value)}
              />
            </Field>
          </div>
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
    </div>
  );
}
