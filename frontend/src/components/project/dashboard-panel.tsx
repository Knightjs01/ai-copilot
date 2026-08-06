"use client";

import Link from "next/link";
import {
  AlertCircle,
  Briefcase,
  CalendarClock,
  ClipboardCheck,
  type LucideIcon,
  TrendingUp,
  Users,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useDashboardStats } from "@/lib/queries/dashboard";
import type { ActionItem, ActionItemType } from "@/lib/types";

const ACTION_ITEM_ICON: Record<ActionItemType, LucideIcon> = {
  ready_to_advance: TrendingUp,
  needs_interview_scheduling: CalendarClock,
  needs_prescreen: ClipboardCheck,
  needs_alignment: AlertCircle,
};

function StatTile({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: number }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-white px-4 py-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand/10 text-brand">
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex flex-col">
        <span className="text-lg font-semibold leading-none tracking-tight text-foreground">
          {value}
        </span>
        <span className="mt-1 text-xs text-muted-foreground">{label}</span>
      </div>
    </div>
  );
}

function ActionItemRow({ item }: { item: ActionItem }) {
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

export function DashboardPanel() {
  const { data, isLoading } = useDashboardStats();

  if (isLoading || !data) {
    return (
      <Card>
        <CardContent className="flex justify-center py-10">
          <Spinner className="h-5 w-5 text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3">
        <StatTile icon={Briefcase} label="Live projects" value={data.live_projects} />
        <StatTile icon={Users} label="Candidates in process" value={data.candidates_in_process} />
        <StatTile
          icon={ClipboardCheck}
          label="Pre-screen stage"
          value={data.prescreen_stage_count}
        />
        <StatTile
          icon={TrendingUp}
          label="Hiring manager stage"
          value={data.hiring_manager_stage_count}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Phantom Action</CardTitle>
          <p className="text-sm text-muted-foreground">
            {data.action_item_count > 0
              ? `${data.action_item_count} thing${data.action_item_count === 1 ? "" : "s"} need${
                  data.action_item_count === 1 ? "s" : ""
                } your attention`
              : "Nothing needs your attention right now."}
          </p>
        </CardHeader>
        {data.action_items.length > 0 && (
          <CardContent className="flex flex-col gap-0.5 pt-0">
            {data.action_items.map((item, index) => (
              <ActionItemRow
                key={`${item.type}-${item.candidate_id ?? item.project_id}-${index}`}
                item={item}
              />
            ))}
          </CardContent>
        )}
      </Card>
    </div>
  );
}
