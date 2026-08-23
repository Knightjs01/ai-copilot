import { formatDistanceToNow } from "date-fns";
import {
  Calendar,
  CircleUser,
  Eye,
  FileCheck,
  History,
  MessageCircle,
  type LucideIcon,
} from "lucide-react";

import { Spinner } from "@/components/ui/spinner";
import { useApplicantActivity } from "@/lib/queries/shadow-jobs";

const ACTION_ICON: Record<string, LucideIcon> = {
  "shadow_application.submitted": FileCheck,
  "shadow_application.added_by_recruiter": FileCheck,
  "shadow_application.withdrawn": FileCheck,
  "shadow_application.pipeline_stage_updated": History,
  "shadow_reveal.requested": Eye,
  "shadow_reveal.approved": Eye,
  "shadow_reveal.declined": Eye,
  "shadow_reveal.identity_viewed": Eye,
  "message.sent": MessageCircle,
  "interview.scheduled": Calendar,
  "interview.rescheduled": Calendar,
  "interview.updated": Calendar,
  "interview.cancelled": Calendar,
  "interview.completed": Calendar,
};

const ACTION_LABEL: Record<string, string> = {
  "shadow_application.submitted": "Application submitted",
  "shadow_application.added_by_recruiter": "Added to pipeline by a recruiter",
  "shadow_application.withdrawn": "Application withdrawn",
  "shadow_application.pipeline_stage_updated": "Pipeline stage updated",
  "shadow_reveal.requested": "Identity reveal requested",
  "shadow_reveal.approved": "Identity revealed",
  "shadow_reveal.declined": "Reveal request declined",
  "shadow_reveal.identity_viewed": "Identity revealed to your team",
  "message.sent": "Message sent",
  "interview.scheduled": "Interview scheduled",
  "interview.rescheduled": "Interview rescheduled",
  "interview.updated": "Interview updated",
  "interview.cancelled": "Interview cancelled",
  "interview.completed": "Interview completed",
};

export function ActivityTab({
  jobId,
  applicationId,
}: {
  jobId: string;
  applicationId: string;
}) {
  const { data: entries, isLoading } = useApplicantActivity(jobId, applicationId);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  if (!entries || entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No activity recorded yet.</p>;
  }

  return (
    <div className="flex flex-col gap-3 border-l border-border pl-4">
      {entries.map((entry) => {
        const Icon = ACTION_ICON[entry.action] ?? History;
        return (
          <div key={entry.id} className="relative">
            <span className="absolute -left-[25px] flex h-6 w-6 items-center justify-center rounded-full bg-secondary">
              <Icon className="h-3 w-3 text-muted-foreground" />
            </span>
            <p className="text-sm text-foreground">{ACTION_LABEL[entry.action] ?? entry.action}</p>
            <p className="flex items-center gap-1 text-xs text-muted-foreground">
              <CircleUser className="h-3 w-3" />
              {entry.actor_email ?? "Candidate"} ·{" "}
              {formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}
            </p>
          </div>
        );
      })}
    </div>
  );
}
