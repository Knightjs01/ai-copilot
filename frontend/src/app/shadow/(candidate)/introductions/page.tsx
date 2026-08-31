"use client";

import Link from "next/link";
import { Handshake, MessageCircle } from "lucide-react";

import { EmptyState } from "@/components/shadow/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  useMyIntroductionRequests,
  useRespondToIntroductionRequest,
} from "@/lib/queries/shadow-introductions";
import { INTRODUCTION_STATUS_LABEL, INTRODUCTION_STATUS_VARIANT } from "@/lib/status-display";
import type { CandidateIntroductionRequestRead } from "@/lib/types";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function PendingIntroductionCard({ request }: { request: CandidateIntroductionRequestRead }) {
  const respond = useRespondToIntroductionRequest(request.id);

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-0.5">
            <h2 className="text-sm font-semibold text-foreground">{request.company_name}</h2>
            <p className="text-xs text-muted-foreground">About: {request.job_title}</p>
          </div>
          <Badge variant={INTRODUCTION_STATUS_VARIANT.pending}>
            {INTRODUCTION_STATUS_LABEL.pending}
          </Badge>
        </div>
        {request.message && (
          <p className="text-sm text-muted-foreground">&ldquo;{request.message}&rdquo;</p>
        )}
        <div className="flex justify-end gap-2 border-t border-border pt-3">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => respond.mutate(false)}
            disabled={respond.isPending}
          >
            Not now
          </Button>
          <Button
            type="button"
            variant="brand"
            size="sm"
            onClick={() => respond.mutate(true)}
            disabled={respond.isPending}
          >
            {respond.isPending ? "Accepting…" : "Accept"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function AcceptedIntroductionCard({ request }: { request: CandidateIntroductionRequestRead }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-2 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-0.5">
            <h2 className="text-sm font-semibold text-foreground">{request.company_name}</h2>
            <p className="text-xs text-muted-foreground">
              {request.job_title} · Accepted {formatDate(request.responded_at!)}
            </p>
          </div>
          <Badge variant={INTRODUCTION_STATUS_VARIANT.accepted}>
            {INTRODUCTION_STATUS_LABEL.accepted}
          </Badge>
        </div>
        {request.resulting_application_id && (
          <div className="flex justify-end">
            <Button type="button" variant="brand" size="sm" asChild>
              <Link href={`/shadow/applications/${request.resulting_application_id}`}>
                <MessageCircle className="mr-1 h-3.5 w-3.5" />
                Open conversation
              </Link>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function DeclinedIntroductionCard({ request }: { request: CandidateIntroductionRequestRead }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1.5 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-0.5">
            <h2 className="text-sm font-semibold text-foreground">{request.company_name}</h2>
            <p className="text-xs text-muted-foreground">{request.job_title}</p>
          </div>
          <Badge variant={INTRODUCTION_STATUS_VARIANT.declined}>
            {INTRODUCTION_STATUS_LABEL.declined}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

// Real data via GET /introductions/my-requests -- the candidate's own accept/decline surface for
// Request Introduction, the "primary conversion action" a recruiter can take on an anonymous
// search result. Kept as its own page (not folded into Talent Memory) since it's a distinct
// consent mechanism: accepting opens a real conversation, Talent Memory never does.
export default function IntroductionsPage() {
  const { data: requests, isLoading } = useMyIntroductionRequests();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Introductions</h1>
        <p className="text-sm text-muted-foreground">
          Companies that would like to start a conversation with you about a specific role. Your
          identity stays private unless you choose to share it later.
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && requests?.length === 0 && (
        <EmptyState
          icon={Handshake}
          title="No introductions yet"
          description="You'll see it here the moment a company wants to connect."
        />
      )}

      <div className="flex flex-col gap-3">
        {requests?.map((request) =>
          request.status === "pending" ? (
            <PendingIntroductionCard key={request.id} request={request} />
          ) : request.status === "accepted" ? (
            <AcceptedIntroductionCard key={request.id} request={request} />
          ) : (
            <DeclinedIntroductionCard key={request.id} request={request} />
          )
        )}
      </div>
    </div>
  );
}
