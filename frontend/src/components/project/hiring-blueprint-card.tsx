"use client";

import { CheckCircle2, Circle, Sparkles } from "lucide-react";

import { AiProvenance } from "@/components/ai-provenance";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useGenerateHiringBlueprint, useHiringBlueprint } from "@/lib/queries/hiring-blueprint";
import { cn } from "@/lib/utils";
import type { Project } from "@/lib/types";

export function ListSection({ title, items }: { title: string; items: string[] }) {
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

// Distinguishes "required" from "nice to have" at a glance — a required item costs the reader
// nothing to skim (tinted panel), an optional one doesn't compete for attention.
function RequirementList({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "required" | "optional";
}) {
  if (items.length === 0) return null;
  const Icon = tone === "required" ? CheckCircle2 : Circle;
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      <ul
        className={cn(
          "flex flex-col gap-1.5 rounded-xl p-3",
          tone === "required" && "border border-success/20 bg-success/5"
        )}
      >
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-foreground">
            <Icon
              className={cn(
                "mt-0.5 h-3.5 w-3.5 shrink-0",
                tone === "required" ? "text-success" : "text-muted-foreground"
              )}
            />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

// Evaluation criteria are ordered assessment steps, not an unordered set — a numbered list
// signals that more accurately than bullets.
function NumberedList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      <ol className="flex flex-col gap-1.5">
        {items.map((item, i) => (
          <li key={i} className="flex gap-2.5 text-sm text-foreground">
            <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-secondary text-[10px] font-semibold text-muted-foreground">
              {i + 1}
            </span>
            {item}
          </li>
        ))}
      </ol>
    </div>
  );
}

export function HiringBlueprintCard({ project }: { project: Project }) {
  const { data: blueprint, isLoading } = useHiringBlueprint(project.id);
  const generate = useGenerateHiringBlueprint(project.id);

  const canGenerate = !!project.role_brief;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>AI hiring blueprint</CardTitle>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => generate.mutate()}
          disabled={!canGenerate || generate.isPending}
        >
          <Sparkles className="h-3.5 w-3.5" />
          {generate.isPending
            ? "Generating…"
            : blueprint
              ? "Regenerate"
              : "Generate blueprint"}
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Spinner className="h-4 w-4 text-muted-foreground" />
        ) : !canGenerate ? (
          <p className="text-sm text-muted-foreground">
            Add a role brief above before generating a blueprint.
          </p>
        ) : !blueprint ? (
          <p className="text-sm text-muted-foreground">
            No blueprint yet. Generate one from the role brief.
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-foreground">{blueprint.role_summary}</p>
            <ListSection title="Key responsibilities" items={blueprint.key_responsibilities} />
            <RequirementList
              title="Must-have qualifications"
              items={blueprint.must_have_qualifications}
              tone="required"
            />
            <RequirementList
              title="Nice-to-have qualifications"
              items={blueprint.nice_to_have_qualifications}
              tone="optional"
            />
            <NumberedList title="Evaluation criteria" items={blueprint.evaluation_criteria} />
            <AiProvenance modelUsed={blueprint.model_used} generatedAt={blueprint.generated_at} />
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
