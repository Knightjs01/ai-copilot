"use client";

import { useParams } from "next/navigation";

import { BurnProjectDialog } from "@/components/project/burn-project-dialog";
import { CandidatesKanban } from "@/components/project/candidates-kanban";
import { HiringBlueprintCard } from "@/components/project/hiring-blueprint-card";
import { HiringManagerAlignmentCard } from "@/components/project/hiring-manager-alignment-card";
import { RoleInfoCard } from "@/components/project/role-info-card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { useProject } from "@/lib/queries/projects";
import { PROJECT_STATUS_LABEL, PROJECT_STATUS_VARIANT } from "@/lib/status-display";

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const { data: project, isLoading } = useProject(params.id);

  if (isLoading || !project) {
    return (
      <div className="flex justify-center py-24">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            {project.title}
          </h1>
          <Badge variant={PROJECT_STATUS_VARIANT[project.status]}>
            {PROJECT_STATUS_LABEL[project.status]}
          </Badge>
        </div>
        <BurnProjectDialog projectId={project.id} projectTitle={project.title} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <RoleInfoCard project={project} />
        <HiringBlueprintCard project={project} />
        <HiringManagerAlignmentCard projectId={project.id} />
      </div>

      <CandidatesKanban projectId={project.id} />
    </div>
  );
}
