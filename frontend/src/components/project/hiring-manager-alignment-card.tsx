"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Plus, X } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  useHiringManagerAlignment,
  useSubmitHiringManagerAlignment,
} from "@/lib/queries/hiring-manager-alignment";

const MAX_REQUIREMENTS = 5;

export function HiringManagerAlignmentCard({ projectId }: { projectId: string }) {
  const router = useRouter();
  const { data: alignment, isLoading } = useHiringManagerAlignment(projectId);
  const submit = useSubmitHiringManagerAlignment(projectId);

  const [requirements, setRequirements] = React.useState<string[]>([""]);
  const [isDirty, setIsDirty] = React.useState(false);

  React.useEffect(() => {
    if (!isDirty && alignment) setRequirements(alignment.top_requirements);
  }, [alignment, isDirty]);

  const updateAt = (index: number, value: string) => {
    setRequirements((prev) => prev.map((r, i) => (i === index ? value : r)));
    setIsDirty(true);
  };

  const removeAt = (index: number) => {
    setRequirements((prev) => prev.filter((_, i) => i !== index));
    setIsDirty(true);
  };

  const addRow = () => {
    setRequirements((prev) => [...prev, ""]);
    setIsDirty(true);
  };

  const handleSave = () => {
    const cleaned = requirements.map((r) => r.trim()).filter(Boolean);
    if (cleaned.length === 0) return;
    submit.mutate(cleaned, { onSuccess: () => setIsDirty(false) });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Hiring manager alignment</CardTitle>
        <p className="text-sm text-muted-foreground">
          What did the hiring manager say matters most? Top 5, in their words.
        </p>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {!isLoading &&
          requirements.map((req, i) => (
            <div key={i} className="flex items-center gap-2">
              <Input
                value={req}
                placeholder={`Requirement ${i + 1}`}
                onChange={(e) => updateAt(i, e.target.value)}
              />
              {requirements.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeAt(i)}
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                  aria-label="Remove requirement"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}

        <div className="flex items-center justify-between pt-1">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={addRow}
            disabled={requirements.length >= MAX_REQUIREMENTS}
          >
            <Plus className="h-3.5 w-3.5" />
            Add requirement
          </Button>
          <Button size="sm" onClick={handleSave} disabled={!isDirty || submit.isPending}>
            {submit.isPending ? "Saving…" : "Save"}
          </Button>
        </div>

        {alignment && !isDirty && (
          <p className="text-xs text-muted-foreground">
            Last saved {formatDistanceToNow(new Date(alignment.submitted_at), { addSuffix: true })}
          </p>
        )}

        <Button
          type="button"
          variant="secondary"
          className="mt-1 self-start"
          onClick={() => router.push(`/projects/${projectId}?tab=blueprint`)}
        >
          Create Hiring Blueprint
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </CardContent>
    </Card>
  );
}
