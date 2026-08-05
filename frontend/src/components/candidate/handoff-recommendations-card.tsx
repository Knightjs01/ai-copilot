"use client";

import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useGenerateHandoffRecommendations,
  usePrescreenAssessment,
} from "@/lib/queries/prescreen-assessment";
import type { Candidate } from "@/lib/types";

export function HandoffRecommendationsCard({ candidate }: { candidate: Candidate }) {
  const { data: assessment } = usePrescreenAssessment(candidate.id);
  const generate = useGenerateHandoffRecommendations(candidate.id);

  const canGenerate = !!assessment && !!candidate.prescreen_notes;

  const missingReason = !assessment
    ? "Generate the pre-screen fit assessment first."
    : !candidate.prescreen_notes
      ? "Save your pre-screen call notes above first."
      : null;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Handoff to hiring manager</CardTitle>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => generate.mutate()}
          disabled={!canGenerate || generate.isPending}
        >
          <Sparkles className="h-3.5 w-3.5" />
          {generate.isPending
            ? "Generating…"
            : assessment?.handoff_recommendations
              ? "Regenerate"
              : "Generate recommendations"}
        </Button>
      </CardHeader>
      <CardContent>
        {missingReason && !assessment?.handoff_recommendations ? (
          <p className="text-sm text-muted-foreground">{missingReason}</p>
        ) : !assessment?.handoff_recommendations ? (
          <p className="text-sm text-muted-foreground">Not generated yet.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {assessment.handoff_recommendations.map((rec, i) => (
              <li key={i} className="flex gap-2 text-sm text-foreground">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
                {rec}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
