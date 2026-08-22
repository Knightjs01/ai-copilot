"use client";

import Link from "next/link";
import { ArrowRight, BarChart3 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useDashboardStats } from "@/lib/queries/dashboard";
import { useProjects } from "@/lib/queries/projects";
import { PROJECT_STATUS_LABEL, PROJECT_STATUS_VARIANT } from "@/lib/status-display";
import { Badge } from "@/components/ui/badge";

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-border bg-card p-4">
      <p className="text-2xl font-semibold text-foreground">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

export default function AnalyticsPage() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: projects, isLoading: projectsLoading } = useProjects();

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight text-foreground">
          <BarChart3 className="h-5 w-5 text-brand" />
          Analytics
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Company-wide totals, plus a link into each job&apos;s own detailed analytics.
        </p>
      </div>

      {statsLoading ? (
        <Spinner className="h-5 w-5 text-muted-foreground" />
      ) : stats ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatTile label="Live roles" value={stats.live_projects} />
          <StatTile label="Candidates in process" value={stats.candidates_in_process} />
          <StatTile label="Pre-screen stage" value={stats.prescreen_stage_count} />
          <StatTile label="Hiring-manager stage" value={stats.hiring_manager_stage_count} />
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Not yet available</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Time to Hire, Source Performance, Team Performance, and Forecast are roadmap items —
            no cross-project analytics backend exists for them yet. Each job&apos;s own analytics
            (pipeline breakdown, fit-rating distribution, salary stats) is real today, below.
          </p>
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Per-job analytics
        </h2>
        {projectsLoading ? (
          <Spinner className="h-5 w-5 text-muted-foreground" />
        ) : (
          <div className="flex flex-col gap-2">
            {(projects ?? []).map((project) => (
              <Link key={project.id} href={`/projects/${project.id}`}>
                <Card className="transition-colors hover:border-brand">
                  <CardContent className="flex items-center justify-between gap-3 py-3.5">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-foreground">{project.title}</span>
                      <Badge variant={PROJECT_STATUS_VARIANT[project.status]}>
                        {PROJECT_STATUS_LABEL[project.status]}
                      </Badge>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
