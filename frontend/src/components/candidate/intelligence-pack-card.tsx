"use client";

import { Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useSanitizedProfile } from "@/lib/queries/privacy-gateway";
import { useGenerateIntelligencePack, useIntelligencePack } from "@/lib/queries/intelligence";

export function IntelligencePackCard({ candidateId }: { candidateId: string }) {
  const { data: sanitizedProfile } = useSanitizedProfile(candidateId);
  const { data: pack, isLoading } = useIntelligencePack(candidateId);
  const generate = useGenerateIntelligencePack(candidateId);

  const canGenerate = !!sanitizedProfile;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Candidate intelligence pack</CardTitle>
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
          <p className="text-sm text-muted-foreground">
            Sanitize the resume above before generating the intelligence pack.
          </p>
        ) : !pack ? (
          <p className="text-sm text-muted-foreground">Not generated yet.</p>
        ) : (
          <div className="flex flex-col gap-4">
            <div>
              <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Skills
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
              <p className="text-sm text-foreground">{pack.experience_summary}</p>
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
              <p className="text-sm text-foreground">{pack.narrative_summary}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
