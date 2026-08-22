"use client";

import * as React from "react";
import Link from "next/link";
import { Briefcase } from "lucide-react";

import { NewProjectDialog } from "@/components/new-project-dialog";
import { DashboardPanel } from "@/components/project/dashboard-panel";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useProjects } from "@/lib/queries/projects";
import { PROJECT_STATUS_LABEL, PROJECT_STATUS_VARIANT } from "@/lib/status-display";
import { cn } from "@/lib/utils";
import type { Project, ProjectStatus } from "@/lib/types";

// The real ProjectStatus enum -- no "Archived" chip, that status doesn't exist.
const STATUS_FILTERS: { value: ProjectStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "open", label: "Open" },
  { value: "draft", label: "Draft" },
  { value: "on_hold", label: "Paused" },
  { value: "filled", label: "Filled" },
  { value: "cancelled", label: "Cancelled" },
];

function ProjectCard({ project }: { project: Project }) {
  return (
    <Link href={`/projects/${project.id}`}>
      <Card className="h-full transition-shadow hover:shadow-md hover:shadow-slate-900/[0.06]">
        <CardHeader className="flex-row items-start justify-between gap-2">
          <CardTitle>{project.title}</CardTitle>
          <Badge variant={PROJECT_STATUS_VARIANT[project.status]}>
            {PROJECT_STATUS_LABEL[project.status]}
          </Badge>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {project.department || "No department set"}
          </p>
        </CardContent>
      </Card>
    </Link>
  );
}

function ProjectGroup({ title, projects }: { title: string; projects: Project[] }) {
  if (projects.length === 0) return null;
  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </div>
  );
}

export default function ProjectsPage() {
  const { data: projects, isLoading } = useProjects();
  const [statusFilter, setStatusFilter] = React.useState<ProjectStatus | "all">("all");

  const filtered =
    statusFilter === "all" ? projects ?? [] : (projects ?? []).filter((p) => p.status === statusFilter);

  const live = filtered.filter((p) => p.status === "open");
  const draft = filtered.filter((p) => p.status === "draft");
  const other = filtered.filter((p) => p.status !== "open" && p.status !== "draft");

  return (
    <div className="grid grid-cols-1 gap-8 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="flex flex-col gap-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              Hiring projects
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Manage pre-screen for every open role.
            </p>
          </div>
          <NewProjectDialog />
        </div>

        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setStatusFilter(f.value)}
              className={cn(
                "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
                statusFilter === f.value
                  ? "bg-brand/10 text-brand"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="flex justify-center py-24">
            <Spinner className="h-6 w-6 text-muted-foreground" />
          </div>
        ) : filtered.length > 0 ? (
          <div className="flex flex-col gap-8">
            <ProjectGroup title="Live" projects={live} />
            <ProjectGroup title="Draft" projects={draft} />
            <ProjectGroup title="Other" projects={other} />
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
            <Briefcase className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm font-medium text-foreground">No hiring projects yet</p>
            <p className="max-w-xs text-sm text-muted-foreground">
              Create your first project to start screening candidates.
            </p>
          </div>
        )}
      </div>

      <DashboardPanel />
    </div>
  );
}
