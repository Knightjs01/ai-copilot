"use client";

import * as React from "react";
import Link from "next/link";
import { format, isToday } from "date-fns";
import { Calendar, ShieldAlert, Video } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";
import { useCompanyInterviews } from "@/lib/queries/shadow-jobs";
import { INTERVIEW_STATUS_LABEL, INTERVIEW_STATUS_VARIANT } from "@/lib/status-display";
import type { CompanyInterviewSummary } from "@/lib/types";

type Filter = "upcoming" | "today" | "awaiting_feedback" | "completed";

const FILTERS: { value: Filter; label: string }[] = [
  { value: "upcoming", label: "Upcoming" },
  { value: "today", label: "Today" },
  { value: "awaiting_feedback", label: "Awaiting Feedback" },
  { value: "completed", label: "Completed" },
];

function matchesFilter(interview: CompanyInterviewSummary, filter: Filter): boolean {
  const scheduledAt = new Date(interview.scheduled_at);
  switch (filter) {
    case "upcoming":
      return interview.status === "scheduled" && scheduledAt > new Date();
    case "today":
      return interview.status === "scheduled" && isToday(scheduledAt);
    // No separate "feedback submitted" flag exists anywhere in this codebase -- completed
    // interviews are the honest proxy for "may need a Handoff Recommendation."
    case "awaiting_feedback":
      return interview.status === "completed";
    case "completed":
      return interview.status === "completed";
  }
}

function InterviewRow({ interview }: { interview: CompanyInterviewSummary }) {
  return (
    <Link href={`/interviews/${interview.id}`}>
      <Card className="transition-colors hover:border-brand">
        <CardContent className="flex flex-col gap-1 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-foreground">{interview.job_title}</p>
            <p className="truncate text-xs text-muted-foreground">{interview.callsign}</p>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <span className="text-xs text-muted-foreground">
              {format(new Date(interview.scheduled_at), "EEE d MMM, HH:mm")}
            </span>
            <Badge variant={INTERVIEW_STATUS_VARIANT[interview.status]}>
              {INTERVIEW_STATUS_LABEL[interview.status]}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

export default function InterviewsPage() {
  const { hasPermission } = useAuth();
  const canView = hasPermission("interviews.view");
  const [filter, setFilter] = React.useState<Filter>("upcoming");
  const { data: interviews, isLoading } = useCompanyInterviews({ enabled: canView });

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Interviews aren&apos;t available on your role</p>
      </div>
    );
  }

  const filtered = (interviews ?? []).filter((i) => matchesFilter(i, filter));

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight text-foreground">
          <Video className="h-5 w-5 text-brand" />
          Interviews
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Every scheduled interview across every job, company-wide.
        </p>
      </div>

      <div className="flex gap-2 border-b border-border pb-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setFilter(f.value)}
            className={
              "rounded-full px-3 py-1.5 text-sm font-medium transition-colors " +
              (filter === f.value
                ? "bg-brand/10 text-brand"
                : "text-muted-foreground hover:text-foreground")
            }
          >
            {f.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <Spinner className="h-5 w-5 text-muted-foreground" />
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-16 text-center">
          <Calendar className="h-6 w-6 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No interviews in this view.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {filtered.map((interview) => (
            <InterviewRow key={interview.id} interview={interview} />
          ))}
        </div>
      )}
    </div>
  );
}
