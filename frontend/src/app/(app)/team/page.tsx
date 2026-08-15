"use client";

import { CheckCircle2, CircleDashed } from "lucide-react";

import { InviteTeammateDialog } from "@/components/invite-teammate-dialog";
import { RemoveMemberDialog } from "@/components/team/remove-member-dialog";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { StatTile } from "@/components/ui/stat-tile";
import { useAuth } from "@/lib/auth-context";
import { useChangeRole, useTeam } from "@/lib/queries/team";
import { ROLE_LABEL, ROLE_VARIANT } from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import type { RoleName } from "@/lib/types";

const ROLE_OPTIONS: RoleName[] = ["Member", "Admin", "Owner"];

function RoleSelect({ userId, role }: { userId: string; role: RoleName }) {
  const changeRole = useChangeRole(userId);
  const container = useThemeScopeContainer();

  return (
    <Select value={role} onValueChange={(value) => changeRole.mutate(value as RoleName)}>
      <SelectTrigger className="h-8 w-32 text-xs">
        <SelectValue />
      </SelectTrigger>
      <SelectContent container={container}>
        {ROLE_OPTIONS.map((option) => (
          <SelectItem key={option} value={option}>
            {ROLE_LABEL[option]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export default function TeamPage() {
  const { data: team, isLoading } = useTeam();
  const { user, hasPermission } = useAuth();
  const canChangeRole = hasPermission("users.change_role");
  const canRemove = hasPermission("users.remove");

  const pendingCount = team?.filter((m) => !m.is_email_verified).length ?? 0;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Team</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Everyone here sees the same hiring projects and candidates.
          </p>
        </div>
        {hasPermission("users.invite") && <InviteTeammateDialog />}
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-8">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
          <Skeleton className="h-48 w-full" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <StatTile label="Team members" value={team?.length ?? 0} />
            <StatTile label="Pending invites" value={pendingCount} />
          </div>

          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col divide-y divide-border">
                {team?.map((member) => {
                  const isSelf = member.id === user?.id;
                  const primaryRole = (member.roles[0] as RoleName) ?? "Member";
                  return (
                    <div
                      key={member.id}
                      className="flex items-center justify-between gap-4 py-3.5"
                    >
                      <div className="flex items-center gap-3">
                        <Avatar name={member.full_name} />
                        <div>
                          <p className="text-sm font-medium text-foreground">
                            {member.full_name}
                          </p>
                          <p className="text-sm text-muted-foreground">{member.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {canChangeRole && !isSelf ? (
                          <RoleSelect userId={member.id} role={primaryRole} />
                        ) : (
                          member.roles.map((role) => (
                            <Badge key={role} variant={ROLE_VARIANT[role as RoleName]}>
                              {ROLE_LABEL[role as RoleName] ?? role}
                            </Badge>
                          ))
                        )}
                        {member.is_email_verified ? (
                          <span
                            className="flex items-center gap-1 text-xs text-muted-foreground"
                            title="Email verified"
                          >
                            <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                            Verified
                          </span>
                        ) : (
                          <span
                            className="flex items-center gap-1 text-xs text-muted-foreground"
                            title="Invite pending"
                          >
                            <CircleDashed className="h-3.5 w-3.5" />
                            Pending
                          </span>
                        )}
                        {canRemove && !isSelf && (
                          <RemoveMemberDialog userId={member.id} fullName={member.full_name} />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
