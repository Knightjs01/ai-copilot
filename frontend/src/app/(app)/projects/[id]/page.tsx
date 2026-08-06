"use client";

import * as React from "react";
import { useParams } from "next/navigation";

import { BurnProjectDialog } from "@/components/project/burn-project-dialog";
import { CandidatesKanban } from "@/components/project/candidates-kanban";
import { HiringBlueprintCard } from "@/components/project/hiring-blueprint-card";
import { HiringManagerAlignmentCard } from "@/components/project/hiring-manager-alignment-card";
import { IdentityVaultTab } from "@/components/project/identity-vault-tab";
import { ProjectAnalyticsCard } from "@/components/project/project-analytics-card";
import { RoleInfoCard } from "@/components/project/role-info-card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Tabs } from "@/components/ui/tabs";
import { useAuth } from "@/lib/auth-context";
import { useProject } from "@/lib/queries/projects";
import { PROJECT_STATUS_LABEL, PROJECT_STATUS_VARIANT } from "@/lib/status-display";

type ProjectTab = "overview" | "blueprint" | "vault";

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const { data: project, isLoading } = useProject(params.id);
  const [activeTab, setActiveTab] = React.useState<ProjectTab>("overview");
  const { hasPermission } = useAuth();
  const canRevealIdentity = hasPermission("identity_vault.reveal");

  const tabOptions: { value: ProjectTab; label: string }[] = [
    { value: "overview", label: "Overview" },
    { value: "blueprint", label: "AI Hiring Blueprint" },
    ...(canRevealIdentity ? [{ value: "vault" as const, label: "Identity Vault" }] : []),
  ];

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

      <Tabs options={tabOptions} value={activeTab} onChange={setActiveTab} />

      {activeTab === "overview" && (
        <>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <RoleInfoCard project={project} />
            <HiringManagerAlignmentCard projectId={project.id} />
          </div>

          <ProjectAnalyticsCard projectId={project.id} />

          <CandidatesKanban projectId={project.id} />
        </>
      )}

      {activeTab === "blueprint" && <HiringBlueprintCard project={project} />}

      {activeTab === "vault" && canRevealIdentity && <IdentityVaultTab projectId={project.id} />}
    </div>
  );
}
