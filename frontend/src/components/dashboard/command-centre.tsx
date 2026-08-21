"use client";

import { ActionItemRow } from "@/components/dashboard/action-item-row";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatTile } from "@/components/ui/stat-tile";
import { useAuth } from "@/lib/auth-context";
import { useDashboardStats } from "@/lib/queries/dashboard";

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

// Template-built from already-fetched, real data -- zero new LLM call. A page-load-triggered
// generative call would be a first for this codebase (every existing AI feature here is
// user-triggered via an explicit "Generate" button) and risks inventing phrasing not traceable
// to real numbers, exactly the fabrication risk this codebase's forced-template precedents
// (e.g. the Shadow Co-Pilot's summarize_applications) exist to avoid.
function buildBriefing(data: {
  live_projects: number;
  candidates_in_process: number;
  action_item_count: number;
  action_items: { message: string }[];
}): string {
  const roles = `${data.live_projects} live role${data.live_projects === 1 ? "" : "s"}`;
  const candidates = `${data.candidates_in_process} candidate${
    data.candidates_in_process === 1 ? "" : "s"
  } moving through them`;
  if (data.action_item_count === 0) {
    return `${roles}, ${candidates}. Nothing needs your attention right now.`;
  }
  const things = `${data.action_item_count} thing${
    data.action_item_count === 1 ? "" : "s"
  } need${data.action_item_count === 1 ? "s" : ""} your attention today`;
  const first = data.action_items[0]?.message;
  return `${roles}, ${candidates}. ${things}${first ? `, starting with ${first.toLowerCase()}` : ""}.`;
}

export function CommandCentre() {
  const { user } = useAuth();
  const { data, isLoading } = useDashboardStats();

  if (isLoading || !data) {
    return (
      <div className="flex flex-col gap-8">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-48 w-full" />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      </div>
    );
  }

  const firstName = user?.full_name.split(" ")[0] ?? "there";

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {greeting()}, {firstName}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">Here&apos;s what needs your attention.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Phantom AI Briefing</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-foreground">{buildBriefing(data)}</p>
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-3 text-sm font-semibold tracking-tight text-foreground">
          Today&apos;s Priorities
        </h2>
        <Card>
          {data.action_items.length > 0 ? (
            <CardContent className="flex flex-col gap-0.5 py-3">
              {data.action_items.map((item, index) => (
                <ActionItemRow
                  key={`${item.type}-${item.candidate_id ?? item.project_id}-${index}`}
                  item={item}
                />
              ))}
            </CardContent>
          ) : (
            <CardContent className="py-10 text-center">
              <p className="text-sm text-muted-foreground">Nothing needs your attention right now.</p>
            </CardContent>
          )}
        </Card>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold tracking-tight text-foreground">
          Hiring Snapshot
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile label="Live roles" value={data.live_projects} />
          <StatTile label="Candidates in process" value={data.candidates_in_process} />
          <StatTile label="Pre-screen stage" value={data.prescreen_stage_count} />
          <StatTile label="Hiring manager stage" value={data.hiring_manager_stage_count} />
        </div>
      </div>
    </div>
  );
}
