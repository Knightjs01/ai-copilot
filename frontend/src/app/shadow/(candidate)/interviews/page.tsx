"use client";

import { format } from "date-fns";
import { CalendarClock, Sparkles } from "lucide-react";

import { useShadowCopilot } from "@/components/shadow/shadow-copilot-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useMyInterviews } from "@/lib/queries/interviews";
import { INTERVIEW_STATUS_LABEL, INTERVIEW_STATUS_VARIANT } from "@/lib/status-display";
import type { CandidateInterviewSummary } from "@/lib/types";

function InterviewCard({ interview }: { interview: CandidateInterviewSummary }) {
  const { open } = useShadowCopilot();

  return (
    <Card>
      <CardContent className="flex flex-col gap-4 py-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex flex-col gap-0.5">
          <h3 className="text-base font-semibold text-foreground">{interview.job_title}</h3>
          <p className="text-sm text-muted-foreground">{interview.company_name}</p>
          <p className="text-sm text-foreground">
            {format(new Date(interview.scheduled_at), "EEEE d MMMM yyyy, h:mm a")}
          </p>
          {interview.location && (
            <p className="text-sm text-muted-foreground">{interview.location}</p>
          )}
          {interview.meeting_link && (
            <a
              href={interview.meeting_link}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-brand underline underline-offset-2"
            >
              {interview.meeting_link}
            </a>
          )}
          {interview.status === "scheduled" && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="mt-1 w-fit"
              onClick={() => open({ type: "interview", id: interview.id })}
            >
              <Sparkles className="h-3.5 w-3.5" />
              Prep with AI
            </Button>
          )}
        </div>
        <Badge variant={INTERVIEW_STATUS_VARIANT[interview.status]}>
          {INTERVIEW_STATUS_LABEL[interview.status]}
        </Badge>
      </CardContent>
    </Card>
  );
}

export default function MyInterviewsPage() {
  const { data: interviews, isLoading } = useMyInterviews();

  const now = Date.now();
  const upcoming = (interviews ?? [])
    .filter((i) => i.status === "scheduled" && new Date(i.scheduled_at).getTime() >= now)
    .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime());
  const past = (interviews ?? [])
    .filter((i) => i.status !== "scheduled" || new Date(i.scheduled_at).getTime() < now)
    .sort((a, b) => new Date(b.scheduled_at).getTime() - new Date(a.scheduled_at).getTime());

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">My Interviews</h1>
        <p className="text-sm text-muted-foreground">
          Interviews companies have scheduled with you.
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && interviews?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
            <CalendarClock className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              No interviews scheduled yet. They&apos;ll show up here once a company sets one up.
            </p>
          </CardContent>
        </Card>
      )}

      {upcoming.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Upcoming
          </h2>
          <div className="flex flex-col gap-3">
            {upcoming.map((interview) => (
              <InterviewCard key={interview.id} interview={interview} />
            ))}
          </div>
        </div>
      )}

      {past.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Past
          </h2>
          <div className="flex flex-col gap-3">
            {past.map((interview) => (
              <InterviewCard key={interview.id} interview={interview} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
