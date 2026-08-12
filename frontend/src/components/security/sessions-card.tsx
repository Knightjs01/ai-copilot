"use client";

import * as React from "react";
import { formatDistanceToNow } from "date-fns";
import { Laptop, LogOut } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useRevokeOtherSessions, useRevokeSession, useSessions } from "@/lib/queries/security";

function describeDevice(userAgent: string | null): string {
  if (!userAgent) return "Unknown device";
  if (/iphone|ipad/i.test(userAgent)) return "iOS device";
  if (/android/i.test(userAgent)) return "Android device";
  if (/macintosh/i.test(userAgent)) return "Mac";
  if (/windows/i.test(userAgent)) return "Windows PC";
  return "Browser session";
}

export function SessionsCard() {
  const { data: sessions, isLoading } = useSessions();
  const revokeSession = useRevokeSession();
  const revokeOthers = useRevokeOtherSessions();

  const otherSessionCount = sessions?.filter((s) => !s.is_current).length ?? 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <CardTitle>Active sessions</CardTitle>
        {otherSessionCount > 0 && (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => revokeOthers.mutate()}
            disabled={revokeOthers.isPending}
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign out other devices
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Spinner className="h-6 w-6 text-muted-foreground" />
          </div>
        ) : (
          <div className="flex flex-col divide-y divide-border">
            {sessions?.map((session) => (
              <div key={session.id} className="flex items-center justify-between gap-4 py-3.5">
                <div className="flex items-center gap-3">
                  <Laptop className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-foreground">
                        {describeDevice(session.user_agent)}
                      </p>
                      {session.is_current && <Badge variant="success">This device</Badge>}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {session.ip_address ?? "Unknown IP"} · last active{" "}
                      {session.last_used_at
                        ? formatDistanceToNow(new Date(session.last_used_at), { addSuffix: true })
                        : "recently"}
                    </p>
                  </div>
                </div>
                {!session.is_current && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => revokeSession.mutate(session.id)}
                    disabled={revokeSession.isPending}
                  >
                    Revoke
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
