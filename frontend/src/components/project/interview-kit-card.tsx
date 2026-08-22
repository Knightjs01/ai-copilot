"use client";

import * as React from "react";
import { CheckCircle2, Sparkles } from "lucide-react";

import { AiProvenance } from "@/components/ai-provenance";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useHiringBlueprint } from "@/lib/queries/hiring-blueprint";
import {
  useGenerateInterviewKit,
  useInterviewKit,
  useUpdateInterviewKitSelection,
} from "@/lib/queries/interview-kit";
import { useToast } from "@/lib/toast-context";
import { cn } from "@/lib/utils";
import type { InterviewKitQuestion, InterviewKitSourceType, Project } from "@/lib/types";

interface IndexedQuestion extends InterviewKitQuestion {
  index: number;
}

function QuestionCard({
  question,
  selected,
  onToggle,
}: {
  question: IndexedQuestion;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={selected}
      className={cn(
        "flex flex-col gap-2 rounded-xl border p-3 text-left transition-colors",
        selected
          ? "border-brand bg-brand/5"
          : "border-border hover:border-muted-foreground/40 hover:bg-secondary"
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          Grounded in: {question.source_text}
        </span>
        <CheckCircle2
          className={cn(
            "h-4 w-4 shrink-0",
            selected ? "text-brand" : "text-muted-foreground/30"
          )}
        />
      </div>
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
    </button>
  );
}

function QuestionSection({
  title,
  questions,
  sourceType,
  selection,
  onToggle,
}: {
  title: string;
  questions: IndexedQuestion[];
  sourceType: InterviewKitSourceType;
  selection: boolean[];
  onToggle: (index: number) => void;
}) {
  const filtered = questions.filter((q) => q.source_type === sourceType);
  if (filtered.length === 0) return null;
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      <div className="flex flex-col gap-2">
        {filtered.map((q) => (
          <QuestionCard
            key={q.index}
            question={q}
            selected={selection[q.index] ?? false}
            onToggle={() => onToggle(q.index)}
          />
        ))}
      </div>
    </div>
  );
}

export function InterviewKitCard({ project }: { project: Project }) {
  const { data: blueprint } = useHiringBlueprint(project.id);
  const { data: kit, isLoading } = useInterviewKit(project.id);
  const generate = useGenerateInterviewKit(project.id);
  const updateSelection = useUpdateInterviewKitSelection(project.id);
  const toast = useToast();

  const [selection, setSelection] = React.useState<boolean[]>([]);

  // Reset local selection whenever the kit's identity changes (first load, or a fresh
  // regenerate replaces every question) — generated_at is the real signal for "this is a
  // different set of questions now," not just a re-render.
  React.useEffect(() => {
    if (kit) setSelection(kit.questions.map((q) => q.included));
  }, [kit?.generated_at]); // eslint-disable-line react-hooks/exhaustive-deps

  const canGenerate = !!blueprint;
  const selectedCount = selection.filter(Boolean).length;

  const handleBuild = () => {
    updateSelection.mutate(selection, {
      onSuccess: () => {
        toast({
          title: "Pre-screen kit built",
          description: `${selectedCount} question${selectedCount === 1 ? "" : "s"} saved to the kit.`,
        });
      },
      onError: () => {
        toast({
          title: "Couldn't save your selection",
          description: "Try again.",
          variant: "danger",
        });
      },
    });
  };

  const indexedQuestions: IndexedQuestion[] =
    kit?.questions.map((q, index) => ({ ...q, index })) ?? [];

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
            <p className="text-sm text-muted-foreground">
              Select the questions you want your hiring team to ask, then build your kit.
            </p>
            <QuestionSection
              title="Must-have questions"
              questions={indexedQuestions}
              sourceType="must_have"
              selection={selection}
              onToggle={(index) =>
                setSelection((prev) => prev.map((v, i) => (i === index ? !v : v)))
              }
            />
            <QuestionSection
              title="Evaluation criteria questions"
              questions={indexedQuestions}
              sourceType="evaluation_criterion"
              selection={selection}
              onToggle={(index) =>
                setSelection((prev) => prev.map((v, i) => (i === index ? !v : v)))
              }
            />
            <AiProvenance modelUsed={kit.model_used} generatedAt={kit.generated_at} />

            <div className="flex items-center justify-between border-t border-border pt-4">
              <p className="text-xs text-muted-foreground">
                {selectedCount} of {kit.questions.length} question
                {kit.questions.length === 1 ? "" : "s"} selected
              </p>
              <Button
                size="sm"
                onClick={handleBuild}
                disabled={selectedCount === 0 || updateSelection.isPending}
              >
                {updateSelection.isPending ? "Saving…" : "Build my pre-screen kit"}
              </Button>
            </div>
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
