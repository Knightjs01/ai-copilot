"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateCandidate } from "@/lib/queries/candidates";
import { PRESCREEN_OUTCOME_LABEL } from "@/lib/status-display";
import { useToast } from "@/lib/toast-context";
import type { Candidate, PrescreenOutcome } from "@/lib/types";

const OUTCOME_OPTIONS = (Object.keys(PRESCREEN_OUTCOME_LABEL) as PrescreenOutcome[]).map(
  (value) => ({ value, label: PRESCREEN_OUTCOME_LABEL[value] })
);

function toDatetimeLocal(iso: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`;
}

export function PrescreenOutcomeCard({ candidate }: { candidate: Candidate }) {
  const updateCandidate = useUpdateCandidate(candidate.id, candidate.project_id);
  const toast = useToast();

  const [interviewAt, setInterviewAt] = React.useState(
    toDatetimeLocal(candidate.interview_scheduled_at)
  );
  const [outcome, setOutcome] = React.useState<PrescreenOutcome | null>(
    candidate.prescreen_outcome
  );
  const [notes, setNotes] = React.useState(candidate.prescreen_notes ?? "");
  const [isDirty, setIsDirty] = React.useState(false);

  React.useEffect(() => {
    if (isDirty) return;
    setInterviewAt(toDatetimeLocal(candidate.interview_scheduled_at));
    setOutcome(candidate.prescreen_outcome);
    setNotes(candidate.prescreen_notes ?? "");
  }, [candidate, isDirty]);

  const handleSave = () => {
    updateCandidate.mutate(
      {
        interview_scheduled_at: interviewAt ? new Date(interviewAt).toISOString() : undefined,
        prescreen_outcome: outcome ?? undefined,
        prescreen_notes: notes || undefined,
      },
      {
        onSuccess: () => {
          setIsDirty(false);
          toast({ title: "Pre-screen outcome saved", variant: "success" });
        },
      }
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pre-screen outcome</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Field label="Interview scheduled for" htmlFor="interviewAt">
          <Input
            id="interviewAt"
            type="datetime-local"
            value={interviewAt}
            onChange={(e) => {
              setInterviewAt(e.target.value);
              setIsDirty(true);
            }}
          />
        </Field>
        <Field label="Outcome">
          <PillToggleGroup
            options={OUTCOME_OPTIONS}
            value={outcome}
            onChange={(value) => {
              setOutcome(value);
              setIsDirty(true);
            }}
          />
        </Field>
        <Field label="Notes" htmlFor="notes">
          <Textarea
            id="notes"
            rows={5}
            placeholder="What came up on the call?"
            value={notes}
            onChange={(e) => {
              setNotes(e.target.value);
              setIsDirty(true);
            }}
          />
        </Field>
        {updateCandidate.isError && (
          <p className="text-sm font-medium text-danger">Couldn&apos;t save. Try again.</p>
        )}

        <div className="flex justify-end">
          <Button
            size="sm"
            onClick={handleSave}
            disabled={!isDirty || updateCandidate.isPending}
          >
            {updateCandidate.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
