"use client";

import {
  FileText,
  Handshake,
  MessageCircle,
  MessagesSquare,
  ShieldQuestion,
  Users,
  X,
} from "lucide-react";

import { Spinner } from "@/components/ui/spinner";
import { useCandidateTimeline } from "@/lib/queries/candidate-activity";
import type { TimelineEntry, TimelineEventType } from "@/lib/types";

const EVENT_ICON: Record<TimelineEventType, typeof FileText> = {
  application_submitted: FileText,
  reveal_requested: ShieldQuestion,
  reveal_responded: ShieldQuestion,
  talent_pool_requested: Users,
  talent_pool_responded: Users,
  talent_pool_withdrawn: Users,
  passed: X,
  introduction_requested: MessageCircle,
  introduction_responded: Handshake,
  conversation_started: MessagesSquare,
};

function formatOccurredAt(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function TimelineRow({ entry }: { entry: TimelineEntry }) {
  const Icon = EVENT_ICON[entry.event_type];
  return (
    <div className="flex items-start gap-2.5">
      <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
      <div className="flex-1">
        <p className="text-sm text-foreground">{entry.description}</p>
        <p className="text-xs text-muted-foreground">{formatOccurredAt(entry.occurred_at)}</p>
      </div>
    </div>
  );
}

// Your history with this candidate -- only shown once there's real history (see caller). Inserted
// into CandidateQuickViewDialog below the relationship badge.
export function CandidateTimeline({ callsign }: { callsign: string }) {
  const { data: entries, isLoading } = useCandidateTimeline(callsign);

  if (isLoading) {
    return (
      <div className="flex justify-center py-4">
        <Spinner className="h-4 w-4 text-muted-foreground" />
      </div>
    );
  }

  if (!entries || entries.length === 0) return null;

  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Your history with this candidate
      </h4>
      <div className="flex flex-col gap-2.5 rounded-xl border border-border p-3">
        {entries.map((entry, i) => (
          <TimelineRow key={i} entry={entry} />
        ))}
      </div>
    </div>
  );
}
