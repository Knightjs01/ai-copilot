"use client";

import * as React from "react";
import { ShieldAlert, Trash2, UserPlus, Users } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";
import {
  useAddProjectMember,
  useProjectMembers,
  useProjects,
  useRemoveProjectMember,
} from "@/lib/queries/projects";
import { useTeam } from "@/lib/queries/team";
import { ROLE_LABEL, ROLE_VARIANT } from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import type { RoleName } from "@/lib/types";

// Any company teammate can be added -- the backend doesn't restrict membership to the "Hiring
// Manager" role specifically (matches how the single hiring_manager_id slot on EditProjectDialog
// has always worked), but the picker shows each candidate's real role so it's obvious who's who.
function ProjectMembersPanel({
  projectId,
  canManage,
}: {
  projectId: string;
  canManage: boolean;
}) {
  const container = useThemeScopeContainer();
  const { data: team } = useTeam();
  const { data: members, isLoading } = useProjectMembers(projectId);
  const addMember = useAddProjectMember(projectId);
  const removeMember = useRemoveProjectMember(projectId);
  const [pickedUserId, setPickedUserId] = React.useState<string | undefined>(undefined);

  const teamById = new Map((team ?? []).map((u) => [u.id, u]));
  const memberIds = new Set((members ?? []).map((m) => m.user_id));
  const available = (team ?? []).filter((u) => !memberIds.has(u.id));

  const handleAdd = () => {
    if (!pickedUserId) return;
    addMember.mutate(pickedUserId, { onSuccess: () => setPickedUserId(undefined) });
  };

  if (isLoading) {
    return <Spinner className="h-5 w-5 text-muted-foreground" />;
  }

  return (
    <div className="flex flex-col gap-4">
      {members && members.length > 0 ? (
        <div className="flex flex-col gap-2">
          {members.map((member) => {
            const user = teamById.get(member.user_id);
            return (
              <div
                key={member.id}
                className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <Avatar name={user?.full_name ?? "Unknown"} className="h-8 w-8 text-xs" />
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-foreground">
                      {user?.full_name ?? "Former teammate"}
                    </span>
                    {user && <span className="text-xs text-muted-foreground">{user.email}</span>}
                  </div>
                  {user?.roles.map((role) => (
                    <Badge key={role} variant={ROLE_VARIANT[role as RoleName]}>
                      {ROLE_LABEL[role as RoleName] ?? role}
                    </Badge>
                  ))}
                </div>
                {canManage && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeMember.mutate(member.user_id)}
                    disabled={removeMember.isPending}
                    aria-label={`Remove ${user?.full_name ?? "this teammate"}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-border py-10 text-center">
          <Users className="h-5 w-5 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No collaborators added to this role yet.</p>
        </div>
      )}

      {canManage && (
        <div className="flex items-center gap-2">
          <Select value={pickedUserId} onValueChange={setPickedUserId}>
            <SelectTrigger className="max-w-sm">
              <SelectValue placeholder="Add a teammate…" />
            </SelectTrigger>
            <SelectContent container={container}>
              {available.length === 0 ? (
                <div className="px-2 py-1.5 text-sm text-muted-foreground">
                  Everyone on the team is already added.
                </div>
              ) : (
                available.map((u) => (
                  <SelectItem key={u.id} value={u.id}>
                    {u.full_name} · {u.roles.map((r) => ROLE_LABEL[r as RoleName] ?? r).join(", ")}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleAdd}
            disabled={!pickedUserId || addMember.isPending}
          >
            <UserPlus className="h-3.5 w-3.5" />
            Add
          </Button>
        </div>
      )}
    </div>
  );
}

export default function HiringTeamPage() {
  const { hasPermission } = useAuth();
  const container = useThemeScopeContainer();
  const canView = hasPermission("projects.view");
  const canManage = hasPermission("projects.update");
  const { data: projects, isLoading: projectsLoading } = useProjects();
  const [projectId, setProjectId] = React.useState<string | undefined>(undefined);

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">
          Hiring Team isn&apos;t available on your role
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Hiring Team</h1>
        <p className="text-sm text-muted-foreground">
          {canManage
            ? "Allocate hiring managers and other teammates to collaborate on a role."
            : "See who's collaborating on each role."}
        </p>
      </div>

      <div className="max-w-sm">
        <Select value={projectId} onValueChange={setProjectId} disabled={projectsLoading}>
          <SelectTrigger>
            <SelectValue placeholder="Choose a role…" />
          </SelectTrigger>
          <SelectContent container={container}>
            {projects?.map((project) => (
              <SelectItem key={project.id} value={project.id}>
                {project.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!projectId && (
        <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-border py-16 text-center">
          <Users className="h-5 w-5 text-muted-foreground" />
          <p className="text-sm font-medium text-foreground">Pick a role to manage its hiring team</p>
        </div>
      )}

      {projectId && <ProjectMembersPanel projectId={projectId} canManage={canManage} />}
    </div>
  );
}
