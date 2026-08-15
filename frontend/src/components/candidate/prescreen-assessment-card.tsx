"use client";

import { AlertTriangle, CheckCircle2, Sparkles } from "lucide-react";

import { AiProvenance } from "@/components/ai-provenance";
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

// Strengths and gaps sat side-by-side with identical neutral styling before this — visually
// indistinguishable except for the heading, which undercut the point of an at-a-glance fit
// assessment. Amber, not danger-red, for gaps: these are things to probe, not failures.
function ToneList({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "positive" | "caution";
}) {
  if (items.length === 0) return null;
  const Icon = tone === "positive" ? CheckCircle2 : AlertTriangle;
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      <ul
        className={
          tone === "positive"
            ? "flex flex-col gap-1.5 rounded-xl border border-success/20 bg-success/5 p-3"
            : "flex flex-col gap-1.5 rounded-xl border border-warning/20 bg-warning/5 p-3"
        }
      >
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-foreground">
            <Icon
              className={
                tone === "positive"
                  ? "mt-0.5 h-3.5 w-3.5 shrink-0 text-success"
                  : "mt-0.5 h-3.5 w-3.5 shrink-0 text-warning"
              }
            />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

// Signals "ask these in order/individually" more clearly than an undifferentiated bullet list.
function QuestionList({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Suggested questions
      </h4>
      <div className="flex flex-col gap-2">
        {items.map((item, i) => (
          <div
            key={i}
            className="flex items-start gap-2.5 rounded-xl border border-border bg-card p-3"
          >
            <span className="shrink-0 text-xs font-semibold text-brand">Q{i + 1}</span>
            <p className="text-sm text-foreground">{item}</p>
          </div>
        ))}
      </div>
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
            Everything&apos;s ready. Generate the assessment before the call.
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
              <ToneList title="Strengths" items={assessment.strengths} tone="positive" />
              <ToneList title="Gaps" items={assessment.gaps} tone="caution" />
            </div>
            <QuestionList items={assessment.suggested_questions} />
            {assessment.areas_to_probe.length > 0 && (
              <div>
                <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Areas to probe
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {assessment.areas_to_probe.map((area) => (
                    <Badge key={area} variant="outline">
                      {area}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            <AiProvenance modelUsed={assessment.model_used} generatedAt={assessment.generated_at} />
          </div>
        )}
        {generate.isError && (
          <p className="mt-3 text-sm font-medium text-danger">
            Generation failed. Give it another try.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
