"use client";

import * as React from "react";
import { useParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useMyApplication, useWithdrawApplication } from "@/lib/queries/shadow-jobs";
import { useMyRevealRequest, useRespondToRevealRequest } from "@/lib/queries/shadow-reveal";
import {
  SHADOW_APPLICATION_STATUS_LABEL,
  SHADOW_APPLICATION_STATUS_VARIANT,
} from "@/lib/status-display";

export default function ApplicationDetailPage() {
  const params = useParams<{ applicationId: string }>();
  const { data: application, isLoading } = useMyApplication(params.applicationId);
  const { data: revealRequest, isLoading: revealLoading } = useMyRevealRequest(
    params.applicationId
  );
  const withdraw = useWithdrawApplication(params.applicationId);
  const respond = useRespondToRevealRequest(params.applicationId);
  const [respondError, setRespondError] = React.useState<string | null>(null);

  const canWithdraw = application && application.status !== "withdrawn";

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  if (!application) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          Application not found.
        </CardContent>
      </Card>
    );
  }

  const handleRespond = async (approve: boolean) => {
    setRespondError(null);
    try {
      await respond.mutateAsync(approve);
    } catch {
      setRespondError("Couldn't submit your decision. Try again.");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            {application.job_title}
          </h1>
          <p className="text-sm text-muted-foreground">{application.company_name}</p>
          <p className="text-xs text-muted-foreground">Callsign: {application.callsign}</p>
        </div>
        <Badge variant={SHADOW_APPLICATION_STATUS_VARIANT[application.status]}>
          {SHADOW_APPLICATION_STATUS_LABEL[application.status]}
        </Badge>
      </div>

      {!revealLoading && revealRequest && revealRequest.status === "pending" && (
        <Card className="border-brand/30">
          <CardHeader>
            <CardTitle>Reveal Request</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <p className="text-sm text-foreground">
              <strong>{revealRequest.company_name}</strong> wants to see who&apos;s behind{" "}
              {application.callsign}. If you approve, they&apos;ll see your name, email, phone,
              and real employer history. Nothing else.
            </p>
            {revealRequest.reason && (
              <p className="rounded-xl bg-slate-50 p-3 text-sm text-muted-foreground">
                &ldquo;{revealRequest.reason}&rdquo;
              </p>
            )}
            {respondError && <p className="text-sm font-medium text-danger">{respondError}</p>}
            <div className="flex gap-2">
              <Button
                variant="brand"
                onClick={() => handleRespond(true)}
                disabled={respond.isPending}
              >
                Approve reveal
              </Button>
              <Button
                variant="secondary"
                onClick={() => handleRespond(false)}
                disabled={respond.isPending}
              >
                Decline
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!revealLoading && revealRequest && revealRequest.status === "approved" && (
        <Card>
          <CardContent className="py-4 text-sm text-success">
            You approved this reveal. {revealRequest.company_name} can now see your identity.
          </CardContent>
        </Card>
      )}

      {!revealLoading && revealRequest && revealRequest.status === "declined" && (
        <Card>
          <CardContent className="py-4 text-sm text-muted-foreground">
            You declined this reveal request. Your Callsign stays anonymous.
          </CardContent>
        </Card>
      )}

      {canWithdraw && (
        <div className="flex justify-end">
          <Button
            variant="secondary"
            onClick={() => withdraw.mutate()}
            disabled={withdraw.isPending}
          >
            {withdraw.isPending ? "Withdrawing…" : "Withdraw application"}
          </Button>
        </div>
      )}
    </div>
  );
}
