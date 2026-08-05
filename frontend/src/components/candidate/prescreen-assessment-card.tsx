"use client";

import { Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useHiringBlueprint } from "@/lib/queries/hiring-blueprint";
import { useHiringManagerAlignment } from "@/lib/queries/hiring-manager-alignment";
import { useIntelligencePack } from "@/lib/queries/intelligence";
import {
  useGeneratePrescreenAssessment,
  usePrescreenAssessment,
} from "@/lib/queries/prescreen-assessment";
import { FIT_RATING_VARIANT } from "@/lib/status-display";
import type { Candidate } from "@/lib/types";

function ListSection({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      <ul className="flex flex-col gap-1">
        {items.map((item, i) => (
          <li key={i} className="flex gap-2 text-sm text-foreground">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function PrescreenAssessmentCard({ candidate }: { candidate: Candidate }) {
  const { data: pack } = useIntelligencePack(candidate.id);
  const { data: blueprint } = useHiringBlueprint(candidate.project_id);
  const { data: alignment } = useHiringManagerAlignment(candidate.project_id);
  const { data: assessment, isLoading } = usePrescreenAssessment(candidate.id);
  const generate = useGeneratePrescreenAssessment(candidate.id);

  const missing: string[] = [];
  if (!pack) missing.push("the candidate intelligence pack");
  if (!blueprint) missing.push("the project's hiring blueprint");
  if (!alignment) missing.push("the hiring manager alignment");
  const canGenerate = missing.length === 0;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Pre-screen fit assessment</CardTitle>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => generate.mutate()}
          disabled={!canGenerate || generate.isPending}
        >
          <Sparkles className="h-3.5 w-3.5" />
          {generate.isPending ? "Assessing…" : assessment ? "Regenerate" : "Generate assessment"}
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Spinner className="h-4 w-4 text-muted-foreground" />
        ) : !canGenerate ? (
          <p className="text-sm text-muted-foreground">
            Still needed: {missing.join(", ")}.
          </p>
        ) : !assessment ? (
          <p className="text-sm text-muted-foreground">
            Everything&apos;s ready — generate the assessment before the call.
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <Badge variant={FIT_RATING_VARIANT[assessment.fit_rating]}>
                {assessment.fit_rating}
              </Badge>
            </div>
            <p className="text-sm text-foreground">{assessment.fit_summary}</p>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <ListSection title="Strengths" items={assessment.strengths} />
              <ListSection title="Gaps" items={assessment.gaps} />
            </div>
            <ListSection title="Suggested questions" items={assessment.suggested_questions} />
            <ListSection title="Areas to probe" items={assessment.areas_to_probe} />
          </div>
        )}
        {generate.isError && (
          <p className="mt-3 text-sm font-medium text-danger">
            Generation failed — give it another try.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
