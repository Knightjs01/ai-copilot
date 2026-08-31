"use client";

import * as React from "react";
import Link from "next/link";
import { AlertTriangle, Archive, CheckCircle2, Sparkles } from "lucide-react";

import { EmptyState } from "@/components/shadow/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { Spinner } from "@/components/ui/spinner";
import { useTalentPoolOpportunities } from "@/lib/queries/passport-matching";
import {
  useMyTalentPoolRequests,
  useRespondToTalentPoolRequest,
  useWithdrawTalentPoolGrant,
} from "@/lib/queries/talent-pool";
import {
  MATCH_TIER_VARIANT,
  TALENT_POOL_SCOPE_LABEL,
  TALENT_POOL_STATUS_LABEL,
  TALENT_POOL_STATUS_VARIANT,
} from "@/lib/status-display";
import type { CandidateTalentPoolRequest, TalentPoolOpportunity, TalentPoolScope } from "@/lib/types";

const SCOPE_OPTIONS = (Object.keys(TALENT_POOL_SCOPE_LABEL) as TalentPoolScope[]).map((value) => ({
  value,
  label: TALENT_POOL_SCOPE_LABEL[value],
}));

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function PendingRequestCard({ request }: { request: CandidateTalentPoolRequest }) {
  const [scope, setScope] = React.useState<TalentPoolScope>("project_only");
  const respond = useRespondToTalentPoolRequest(request.id);

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-0.5">
            <h2 className="text-sm font-semibold text-foreground">{request.company_name}</h2>
            <p className="text-xs text-muted-foreground">Was considered for: {request.source_role_title}</p>
          </div>
          <Badge variant={TALENT_POOL_STATUS_VARIANT.requested}>
            {TALENT_POOL_STATUS_LABEL.requested}
          </Badge>
        </div>
        {request.note && (
          <p className="text-sm text-muted-foreground">&ldquo;{request.note}&rdquo;</p>
        )}
        <div className="flex flex-col gap-2 border-t border-border pt-3">
          <p className="text-xs font-medium text-foreground">
            Who would you like to allow to discover you?
          </p>
          <PillToggleGroup options={SCOPE_OPTIONS} value={scope} onChange={setScope} />
          <div className="flex justify-end gap-2 pt-1">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => respond.mutate({ approve: false })}
              disabled={respond.isPending}
            >
              Not now
            </Button>
            <Button
              type="button"
              variant="brand"
              size="sm"
              onClick={() => respond.mutate({ approve: true, scope })}
              disabled={respond.isPending}
            >
              {respond.isPending ? "Saving…" : "Allow"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function GrantedRequestCard({ request }: { request: CandidateTalentPoolRequest }) {
  const [confirmOpen, setConfirmOpen] = React.useState(false);
  const withdraw = useWithdrawTalentPoolGrant(request.id);

  return (
    <Card>
      <CardContent className="flex flex-col gap-2 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-0.5">
            <h2 className="text-sm font-semibold text-foreground">{request.company_name}</h2>
            <p className="text-xs text-muted-foreground">
              {TALENT_POOL_SCOPE_LABEL[request.scope]} · Since {formatDate(request.responded_at!)}
            </p>
          </div>
          <Badge variant={TALENT_POOL_STATUS_VARIANT.granted}>
            {TALENT_POOL_STATUS_LABEL.granted}
          </Badge>
        </div>
        <div className="flex justify-end">
          <Button type="button" variant="secondary" size="sm" onClick={() => setConfirmOpen(true)}>
            Withdraw
          </Button>
        </div>
      </CardContent>
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Withdraw from {request.company_name}&apos;s Talent Pool?</DialogTitle>
            <DialogDescription>
              They&apos;ll no longer be able to match you against future roles. You can always
              choose to allow this again later.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="danger"
              onClick={() => withdraw.mutate(undefined, { onSuccess: () => setConfirmOpen(false) })}
              disabled={withdraw.isPending}
            >
              {withdraw.isPending ? "Withdrawing…" : "Withdraw"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

function OpportunityCard({ opportunity }: { opportunity: TalentPoolOpportunity }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-0.5">
            <h2 className="text-sm font-semibold text-foreground">{opportunity.job_title}</h2>
            <p className="text-xs text-muted-foreground">{opportunity.company_name}</p>
          </div>
          <Badge variant={MATCH_TIER_VARIANT[opportunity.match_tier]}>
            {opportunity.match_tier}
          </Badge>
        </div>
        <p className="text-sm text-foreground">{opportunity.match_summary}</p>
        {opportunity.strengths.length > 0 && (
          <div>
            <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Strengths
            </h4>
            <ul className="flex flex-col gap-1.5 rounded-xl border border-success/20 bg-success/5 p-3">
              {opportunity.strengths.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
        {opportunity.gaps.length > 0 && (
          <div>
            <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Gaps
            </h4>
            <ul className="flex flex-col gap-1.5 rounded-xl border border-warning/20 bg-warning/5 p-3">
              {opportunity.gaps.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
        <div className="flex justify-end">
          <Button type="button" variant="brand" size="sm" asChild>
            <Link href={`/shadow/jobs/${opportunity.job_id}`}>View &amp; apply</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function DecidedRequestCard({ request }: { request: CandidateTalentPoolRequest }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1.5 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-0.5">
            <h2 className="text-sm font-semibold text-foreground">{request.company_name}</h2>
            <p className="text-xs text-muted-foreground">{request.source_role_title}</p>
          </div>
          <Badge variant={TALENT_POOL_STATUS_VARIANT[request.status]}>
            {TALENT_POOL_STATUS_LABEL[request.status]}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

// The candidate-wide "who's keeping me on file for future roles" view -- real data via
// GET /talent-pool/my-requests. Lives under Passport rather than a new top-level nav
// destination, same precedent as identity-activity/page.tsx one directory up.
export default function TalentMemoryPage() {
  const { data: requests, isLoading } = useMyTalentPoolRequests();
  const { data: opportunities, isLoading: opportunitiesLoading } = useTalentPoolOpportunities();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Talent memory</h1>
        <p className="text-sm text-muted-foreground">
          Companies that have asked to keep your Passport available for future roles, and who
          you&apos;ve chosen to stay discoverable to.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-base font-semibold tracking-tight text-foreground">
            Potential opportunities
          </h2>
        </div>
        {opportunitiesLoading ? (
          <div className="flex justify-center py-8">
            <Spinner className="h-5 w-5 text-muted-foreground" />
          </div>
        ) : opportunities && opportunities.length > 0 ? (
          <div className="flex flex-col gap-3">
            {opportunities.map((opportunity) => (
              <OpportunityCard key={opportunity.job_id} opportunity={opportunity} />
            ))}
          </div>
        ) : (
          <EmptyState icon={Sparkles} title="No potential opportunities right now" />
        )}
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && requests?.length === 0 && (
        <EmptyState
          icon={Archive}
          title="No company has asked to keep your Passport on file yet"
          description="You'll see it here the moment one does."
        />
      )}

      <div className="flex flex-col gap-3">
        {requests?.map((request) =>
          request.status === "requested" ? (
            <PendingRequestCard key={request.id} request={request} />
          ) : request.status === "granted" ? (
            <GrantedRequestCard key={request.id} request={request} />
          ) : (
            <DecidedRequestCard key={request.id} request={request} />
          )
        )}
      </div>
    </div>
  );
}
