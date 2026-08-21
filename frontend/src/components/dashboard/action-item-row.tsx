import Link from "next/link";
import { AlertCircle, CalendarClock, ClipboardCheck, type LucideIcon, TrendingUp } from "lucide-react";

import type { ActionItem, ActionItemType } from "@/lib/types";

export const ACTION_ITEM_ICON: Record<ActionItemType, LucideIcon> = {
  ready_to_advance: TrendingUp,
  needs_interview_scheduling: CalendarClock,
  needs_prescreen: ClipboardCheck,
  needs_alignment: AlertCircle,
};

export function ActionItemRow({ item }: { item: ActionItem }) {
  const Icon = ACTION_ITEM_ICON[item.type];
  const href = item.candidate_id
    ? `/projects/${item.project_id}/candidates/${item.candidate_id}`
    : `/projects/${item.project_id}`;

  return (
    <Link
      href={href}
      className="flex items-start gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors hover:bg-secondary"
    >
      <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" />
      <div className="flex flex-col">
        <span className="text-foreground">{item.message}</span>
        <span className="text-xs text-muted-foreground">{item.project_title}</span>
      </div>
    </Link>
  );
}
