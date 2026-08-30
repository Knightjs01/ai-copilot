"use client";

import * as React from "react";
import { MessageCircle, Sparkles } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { RequestIntroductionDialog } from "@/components/candidate-search/request-introduction-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { PASS_REASON_LABEL } from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { useMyShadowJobs } from "@/lib/queries/shadow-jobs";
import type { RediscoveryCandidate } from "@/lib/types";

// Lighter than CandidateSearchResultCard -- no match score/dimension breakdown, since a
// rediscovery candidate isn't scored against a specific job. Shows the diff, the original pass
// reason, and a job picker + Request Introduction, which is legitimate here because pass
// exclusion is search-listing-only -- action endpoints never check pass status.
export function RediscoveryCandidateCard({ candidate }: { candidate: RediscoveryCandidate }) {
  const container = useThemeScopeContainer();
  const { data: jobs } = useMyShadowJobs();
  const [jobId, setJobId] = React.useState<string | undefined>(undefined);
  const [introOpen, setIntroOpen] = React.useState(false);

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-4">
        <div className="flex items-start gap-3">
          <Avatar name={candidate.callsign} className="mt-0.5 h-8 w-8 shrink-0 text-xs" />
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-sm font-semibold text-foreground">
              {candidate.callsign}
            </h3>
            {candidate.headline && (
              <p className="truncate text-xs text-muted-foreground">{candidate.headline}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Passed
              {candidate.passed_for_job_title ? ` on ${candidate.passed_for_job_title}` : ""}
              {candidate.passed_reason
                ? ` · ${PASS_REASON_LABEL[candidate.passed_reason]}`
                : ""}
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-1 pl-11">
          <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-brand" />
            What&apos;s changed
          </p>
          <ul className="flex flex-col gap-0.5">
            {candidate.changes.map((change, i) => (
              <li key={i} className="text-xs text-foreground">
                • {change}
              </li>
            ))}
          </ul>
        </div>

        <div className="flex flex-wrap items-center gap-2 pl-11">
          <div className="w-48">
            <Select value={jobId} onValueChange={setJobId}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder="Choose a role…" />
              </SelectTrigger>
              <SelectContent container={container}>
                {jobs?.map((job) => (
                  <SelectItem key={job.id} value={job.id}>
                    {job.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <button
            type="button"
            onClick={() => setIntroOpen(true)}
            disabled={!jobId}
            className="flex items-center gap-1 rounded-full bg-brand px-2.5 py-1 text-xs font-medium text-brand-foreground transition-colors hover:bg-brand/90 disabled:cursor-not-allowed disabled:bg-secondary disabled:text-muted-foreground"
          >
            <MessageCircle className="h-3 w-3" />
            Request introduction
          </button>
        </div>

        {jobId && (
          <RequestIntroductionDialog
            open={introOpen}
            onOpenChange={setIntroOpen}
            jobId={jobId}
            callsign={candidate.callsign}
            onDone={() => setIntroOpen(false)}
          />
        )}
      </CardContent>
    </Card>
  );
}
