"use client";

import * as React from "react";
import { useParams, useSearchParams } from "next/navigation";
import { format } from "date-fns";

import { ApproveProjectDialog } from "@/components/project/approve-project-dialog";
import { BurnProjectDialog } from "@/components/project/burn-project-dialog";
import { CandidatesTabSection } from "@/components/project/candidates-tab-section";
import { EditProjectDialog } from "@/components/project/edit-project-dialog";
import { HiringBlueprintCard } from "@/components/project/hiring-blueprint-card";
import { HiringManagerAlignmentCard } from "@/components/project/hiring-manager-alignment-card";
import { IdentityVaultTab } from "@/components/project/identity-vault-tab";
import { InterviewKitCard } from "@/components/project/interview-kit-card";
import { LiveRoleLink } from "@/components/project/live-role-preview";
import { ProjectAnalyticsCard } from "@/components/project/project-analytics-card";
import { PublishToShadowDialog } from "@/components/project/publish-to-shadow-dialog";
import { RoleHealthCard } from "@/components/project/role-health-card";
import { RoleInfoCard } from "@/components/project/role-info-card";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Tabs } from "@/components/ui/tabs";
import { useAuth } from "@/lib/auth-context";
import { useProject, useProjectActivity } from "@/lib/queries/projects";
import { useCompanyInterviews, useProjectShadowJob } from "@/lib/queries/shadow-jobs";
import { INTERVIEW_STATUS_LABEL, INTERVIEW_STATUS_VARIANT } from "@/lib/status-display";

type ProjectTab = "overview" | "blueprint" | "candidates" | "interviews" | "activity" | "vault";
const PROJECT_TABS: ProjectTab[] = [
  "candidates",
  "interviews",
  "activity",
  "overview",
  "blueprint",
  "vault",
];

function ProjectInterviewsTab({ projectId }: { projectId: string }) {
  const { data: interviews, isLoading } = useCompanyInterviews();
  const filtered = (interviews ?? []).filter((i) => i.project_id === projectId);

  if (isLoading) return <Spinner className="h-5 w-5 text-muted-foreground" />;
  if (filtered.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-border py-16 text-center">
        <p className="text-sm text-muted-foreground">No interviews scheduled for this role yet.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {filtered.map((interview) => (
        <Card key={interview.id}>
          <CardContent className="flex flex-col gap-1 py-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm font-medium text-foreground">{interview.callsign}</p>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground">
                {format(new Date(interview.scheduled_at), "EEE d MMM, HH:mm")}
              </span>
              <Badge variant={INTERVIEW_STATUS_VARIANT[interview.status]}>
                {INTERVIEW_STATUS_LABEL[interview.status]}
              </Badge>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ProjectActivityTab({ projectId }: { projectId: string }) {
  const { data: entries, isLoading } = useProjectActivity(projectId);

  if (isLoading) return <Spinner className="h-5 w-5 text-muted-foreground" />;
  if (!entries || entries.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-border py-16 text-center">
        <p className="text-sm text-muted-foreground">No activity recorded for this role yet.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {entries.map((entry) => (
        <div
          key={entry.id}
          className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card px-4 py-3"
        >
          <span className="text-sm text-foreground">{entry.action.replace(/[._]/g, " ")}</span>
          <span className="shrink-0 text-xs text-muted-foreground">
            {format(new Date(entry.created_at), "d MMM yyyy, HH:mm")}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const { data: project, isLoading } = useProject(params.id);
  const { data: shadowJob } = useProjectShadowJob(params.id);
  const [activeTab, setActiveTab] = React.useState<ProjectTab>("candidates");
  const { hasPermission } = useAuth();
  const canRevealIdentity = hasPermission("identity_vault.reveal");
  const canEditProject = hasPermission("projects.update");
  const canPublishToShadow = hasPermission("shadow_jobs.create");

  React.useEffect(() => {
    const tab = searchParams.get("tab");
    if (PROJECT_TABS.includes(tab as ProjectTab)) setActiveTab(tab as ProjectTab);
  }, [searchParams]);

  const tabOptions: { value: ProjectTab; label: string }[] = [
    { value: "candidates", label: "Candidates" },
    { value: "interviews", label: "Interviews" },
    { value: "activity", label: "Activity" },
    { value: "overview", label: "Overview" },
    { value: "blueprint", label: "Blueprint" },
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
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {project.title}
        </h1>
        <div className="flex items-center gap-2">
          {shadowJob?.status === "published" && <LiveRoleLink jobId={shadowJob.id} />}
          {shadowJob?.status === "pending_review" && (
            <Badge variant="warning">Pending review</Badge>
          )}
          {canPublishToShadow && (
            <PublishToShadowDialog project={project} existingShadowJob={shadowJob} />
          )}
          {canEditProject && <EditProjectDialog project={project} />}
          {canEditProject && <ApproveProjectDialog project={project} />}
          <BurnProjectDialog projectId={project.id} projectTitle={project.title} />
        </div>
      </div>

      <Tabs options={tabOptions} value={activeTab} onChange={setActiveTab} />

      {activeTab === "overview" && (
        <>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <RoleInfoCard project={project} />
            <HiringManagerAlignmentCard projectId={project.id} />
          </div>

          <ProjectAnalyticsCard projectId={project.id} />
          <RoleHealthCard projectId={project.id} />
        </>
      )}

      {activeTab === "blueprint" && (
        <>
          <HiringBlueprintCard project={project} />
          <InterviewKitCard project={project} />
        </>
      )}

      {activeTab === "candidates" && <CandidatesTabSection projectId={project.id} />}

      {activeTab === "interviews" && <ProjectInterviewsTab projectId={project.id} />}

      {activeTab === "activity" && <ProjectActivityTab projectId={project.id} />}

      {activeTab === "vault" && canRevealIdentity && <IdentityVaultTab projectId={project.id} />}
    </div>
  );
}
