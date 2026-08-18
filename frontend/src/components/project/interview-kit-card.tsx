"use client";

import { Sparkles } from "lucide-react";

import { AiProvenance } from "@/components/ai-provenance";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useHiringBlueprint } from "@/lib/queries/hiring-blueprint";
import { useGenerateInterviewKit, useInterviewKit } from "@/lib/queries/interview-kit";
import type { InterviewKitQuestion, InterviewKitSourceType, Project } from "@/lib/types";

function QuestionCard({ question }: { question: InterviewKitQuestion }) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-border p-3">
      <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Grounded in: {question.source_text}
      </span>
      <p className="text-sm font-semibold text-foreground">{question.question_text}</p>
      {question.follow_up_prompts.length > 0 && (
        <ul className="flex flex-col gap-1 pl-3">
          {question.follow_up_prompts.map((prompt, i) => (
            <li key={i} className="flex gap-2 text-sm text-muted-foreground">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
              {prompt}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function QuestionSection({
  title,
  questions,
  sourceType,
}: {
  title: string;
  questions: InterviewKitQuestion[];
  sourceType: InterviewKitSourceType;
}) {
  const filtered = questions.filter((q) => q.source_type === sourceType);
  if (filtered.length === 0) return null;
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      <div className="flex flex-col gap-2">
        {filtered.map((q, i) => (
          <QuestionCard key={i} question={q} />
        ))}
      </div>
    </div>
  );
}

export function InterviewKitCard({ project }: { project: Project }) {
  const { data: blueprint } = useHiringBlueprint(project.id);
  const { data: kit, isLoading } = useInterviewKit(project.id);
  const generate = useGenerateInterviewKit(project.id);

  const canGenerate = !!blueprint;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Interview kit</CardTitle>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => generate.mutate()}
          disabled={!canGenerate || generate.isPending}
        >
          <Sparkles className="h-3.5 w-3.5" />
          {generate.isPending ? "Generating…" : kit ? "Regenerate" : "Generate kit"}
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Spinner className="h-4 w-4 text-muted-foreground" />
        ) : !canGenerate ? (
          <p className="text-sm text-muted-foreground">
            Generate a hiring blueprint above before generating an interview kit.
          </p>
        ) : !kit ? (
          <p className="text-sm text-muted-foreground">
            No interview kit yet. Generate one from the hiring blueprint.
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            <QuestionSection
              title="Must-have questions"
              questions={kit.questions}
              sourceType="must_have"
            />
            <QuestionSection
              title="Evaluation criteria questions"
              questions={kit.questions}
              sourceType="evaluation_criterion"
            />
            <AiProvenance modelUsed={kit.model_used} generatedAt={kit.generated_at} />
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
