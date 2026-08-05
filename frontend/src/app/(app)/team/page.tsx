"use client";

import { CheckCircle2, CircleDashed } from "lucide-react";

import { InviteTeammateDialog } from "@/components/invite-teammate-dialog";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";
import { useTeam } from "@/lib/queries/team";

export default function TeamPage() {
  const { data: team, isLoading } = useTeam();
  const { hasPermission } = useAuth();

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

      <Card>
        <CardContent className="pt-6">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner className="h-6 w-6 text-muted-foreground" />
            </div>
          ) : (
            <div className="flex flex-col divide-y divide-border">
              {team?.map((member) => (
                <div key={member.id} className="flex items-center justify-between gap-4 py-3.5">
                  <div>
                    <p className="text-sm font-medium text-foreground">{member.full_name}</p>
                    <p className="text-sm text-muted-foreground">{member.email}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {member.roles.map((role) => (
                      <Badge key={role} variant="neutral">
                        {role}
                      </Badge>
                    ))}
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
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
