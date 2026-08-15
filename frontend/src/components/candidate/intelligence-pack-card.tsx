"use client";

import { Sparkles, Target } from "lucide-react";

import { AiProvenance } from "@/components/ai-provenance";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useHiringManagerAlignment } from "@/lib/queries/hiring-manager-alignment";
import { useGenerateIntelligencePack, useIntelligencePack } from "@/lib/queries/intelligence";
import { useSanitizedProfile } from "@/lib/queries/privacy-gateway";

export function IntelligencePackCard({
  candidateId,
  projectId,
}: {
  candidateId: string;
  projectId: string;
}) {
  const { data: sanitizedProfile } = useSanitizedProfile(candidateId);
  const { data: alignment } = useHiringManagerAlignment(projectId);
  const { data: pack, isLoading } = useIntelligencePack(candidateId);
  const generate = useGenerateIntelligencePack(candidateId);

  const missing: string[] = [];
  if (!sanitizedProfile) missing.push("a sanitized resume");
  if (!alignment) missing.push("the hiring manager's top requirements");
  const canGenerate = missing.length === 0;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Candidate intelligence</CardTitle>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => generate.mutate()}
          disabled={!canGenerate || generate.isPending}
        >
          <Sparkles className="h-3.5 w-3.5" />
          {generate.isPending ? "Generating…" : pack ? "Regenerate" : "Generate"}
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Spinner className="h-4 w-4 text-muted-foreground" />
        ) : !canGenerate ? (
          <p className="text-sm text-muted-foreground">Still needed: {missing.join(", ")}.</p>
        ) : !pack ? (
          <p className="text-sm text-muted-foreground">Not generated yet.</p>
        ) : (
          <div className="flex flex-col gap-4">
            {pack.highlights.length > 0 && (
              <div className="rounded-xl border border-brand/20 bg-brand/5 px-4 py-3">
                <h4 className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-brand">
                  <Target className="h-3.5 w-3.5" />
                  Smart highlights
                </h4>
                <ul className="flex flex-col gap-1.5">
                  {pack.highlights.map((highlight, i) => (
                    <li key={i} className="flex gap-2 text-sm text-foreground">
                      <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand" />
                      {highlight}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div>
              <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Skills matched to hiring manager requirements
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {pack.skills.map((skill) => (
                  <Badge key={skill} variant="outline">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Experience
              </h4>
              <p className="rounded-xl border-l-2 border-border bg-secondary/40 p-3 text-sm text-foreground">
                {pack.experience_summary}
              </p>
            </div>
            {pack.education.length > 0 && (
              <div>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Education
                </h4>
                <ul className="flex flex-col gap-0.5">
                  {pack.education.map((e, i) => (
                    <li key={i} className="text-sm text-foreground">
                      {e.degree} in {e.field}, {e.institution}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div>
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Summary
              </h4>
              <p className="rounded-xl border-l-2 border-border bg-secondary/40 p-3 text-sm text-foreground">
                {pack.narrative_summary}
              </p>
            </div>
            <AiProvenance modelUsed={pack.model_used} generatedAt={pack.generated_at} />
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
