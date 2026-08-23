"use client";

import { CheckCircle2, TriangleAlert } from "lucide-react";

import { AiProvenance } from "@/components/ai-provenance";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useApplicantMatch } from "@/lib/queries/candidate-search";
import { MATCH_TIER_VARIANT } from "@/lib/status-display";

export function MatchTab({ jobId, applicationId }: { jobId: string; applicationId: string }) {
  const { data: match, isLoading, isError } = useApplicantMatch(jobId, applicationId);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  if (isError || !match) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        Couldn&apos;t compute a match for this applicant.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardContent className="flex flex-col gap-3 py-5">
          <div className="flex items-center gap-3">
            <span className="text-3xl font-semibold tracking-tight text-foreground">
              {match.match_score}%
            </span>
            <Badge variant={MATCH_TIER_VARIANT[match.match_tier]}>{match.match_tier}</Badge>
          </div>
          <p className="text-sm text-foreground">{match.summary}</p>
          <AiProvenance modelUsed="Phantom AI" generatedAt={match.generated_at} />
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-success/20 bg-success/5 p-4">
          <div className="mb-2 flex items-center gap-1.5 text-sm font-medium text-success">
            <CheckCircle2 className="h-4 w-4" />
            Why this matches
          </div>
          <ul className="flex flex-col gap-2">
            {match.strengths.map((strength, i) => (
              <li key={i} className="text-sm text-foreground">
                {strength}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-warning/20 bg-warning/5 p-4">
          <div className="mb-2 flex items-center gap-1.5 text-sm font-medium text-warning-foreground">
            <TriangleAlert className="h-4 w-4" />
            Potential considerations
          </div>
          {match.gaps.length > 0 ? (
            <ul className="flex flex-col gap-2">
              {match.gaps.map((gap, i) => (
                <li key={i} className="text-sm text-foreground">
                  {gap}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Nothing notable flagged.</p>
          )}
        </div>
      </div>
    </div>
  );
}
