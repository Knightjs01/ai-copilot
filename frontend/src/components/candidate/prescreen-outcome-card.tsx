"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateCandidate } from "@/lib/queries/candidates";
import { CANDIDATE_SOURCE_LABEL, PRESCREEN_OUTCOME_LABEL } from "@/lib/status-display";
import type { Candidate, CandidateSource, PrescreenOutcome } from "@/lib/types";

const OUTCOME_OPTIONS = (Object.keys(PRESCREEN_OUTCOME_LABEL) as PrescreenOutcome[]).map(
  (value) => ({ value, label: PRESCREEN_OUTCOME_LABEL[value] })
);

const SOURCE_OPTIONS = (Object.keys(CANDIDATE_SOURCE_LABEL) as CandidateSource[]).map((value) => ({
  value,
  label: CANDIDATE_SOURCE_LABEL[value],
}));

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

  const [interviewAt, setInterviewAt] = React.useState(
    toDatetimeLocal(candidate.interview_scheduled_at)
  );
  const [outcome, setOutcome] = React.useState<PrescreenOutcome | null>(
    candidate.prescreen_outcome
  );
  const [notes, setNotes] = React.useState(candidate.prescreen_notes ?? "");
  const [source, setSource] = React.useState<CandidateSource | null>(candidate.source);
  const [agencyName, setAgencyName] = React.useState(candidate.agency_name ?? "");
  const [expectedSalary, setExpectedSalary] = React.useState(
    candidate.expected_salary != null ? String(candidate.expected_salary) : ""
  );
  const [isDirty, setIsDirty] = React.useState(false);

  React.useEffect(() => {
    if (isDirty) return;
    setInterviewAt(toDatetimeLocal(candidate.interview_scheduled_at));
    setOutcome(candidate.prescreen_outcome);
    setNotes(candidate.prescreen_notes ?? "");
    setSource(candidate.source);
    setAgencyName(candidate.agency_name ?? "");
    setExpectedSalary(candidate.expected_salary != null ? String(candidate.expected_salary) : "");
  }, [candidate, isDirty]);

  const handleSave = () => {
    updateCandidate.mutate(
      {
        interview_scheduled_at: interviewAt ? new Date(interviewAt).toISOString() : undefined,
        prescreen_outcome: outcome ?? undefined,
        prescreen_notes: notes || undefined,
        source: source ?? undefined,
        agency_name: source === "agency" ? agencyName || undefined : undefined,
        expected_salary: expectedSalary ? Number(expectedSalary) : undefined,
      },
      { onSuccess: () => setIsDirty(false) }
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
        <Field label="Source">
          <PillToggleGroup
            options={SOURCE_OPTIONS}
            value={source}
            onChange={(value) => {
              setSource(value);
              setIsDirty(true);
            }}
          />
        </Field>
        {source === "agency" && (
          <Field label="Agency name" htmlFor="agencyName">
            <Input
              id="agencyName"
              placeholder="Which agency submitted them?"
              value={agencyName}
              onChange={(e) => {
                setAgencyName(e.target.value);
                setIsDirty(true);
              }}
            />
          </Field>
        )}
        <Field label="Expected salary" htmlFor="expectedSalary">
          <Input
            id="expectedSalary"
            type="number"
            min={0}
            placeholder="e.g. 95000"
            value={expectedSalary}
            onChange={(e) => {
              setExpectedSalary(e.target.value);
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
