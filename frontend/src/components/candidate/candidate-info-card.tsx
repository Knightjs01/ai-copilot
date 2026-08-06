"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { useUpdateCandidate } from "@/lib/queries/candidates";
import { CANDIDATE_SOURCE_LABEL, NOTICE_PERIOD_LABEL } from "@/lib/status-display";
import type { Candidate, CandidateSource, NoticePeriod } from "@/lib/types";

const SOURCE_OPTIONS = (Object.keys(CANDIDATE_SOURCE_LABEL) as CandidateSource[]).map((value) => ({
  value,
  label: CANDIDATE_SOURCE_LABEL[value],
}));

const NOTICE_PERIOD_OPTIONS = (Object.keys(NOTICE_PERIOD_LABEL) as NoticePeriod[]).map(
  (value) => ({ value, label: NOTICE_PERIOD_LABEL[value] })
);

export function CandidateInfoCard({ candidate }: { candidate: Candidate }) {
  const updateCandidate = useUpdateCandidate(candidate.id, candidate.project_id);

  const [expectedSalary, setExpectedSalary] = React.useState(
    candidate.expected_salary != null ? String(candidate.expected_salary) : ""
  );
  const [noticePeriod, setNoticePeriod] = React.useState<NoticePeriod | null>(
    candidate.notice_period
  );
  const [source, setSource] = React.useState<CandidateSource | null>(candidate.source);
  const [agencyName, setAgencyName] = React.useState(candidate.agency_name ?? "");
  const [isDirty, setIsDirty] = React.useState(false);

  React.useEffect(() => {
    if (isDirty) return;
    setExpectedSalary(candidate.expected_salary != null ? String(candidate.expected_salary) : "");
    setNoticePeriod(candidate.notice_period);
    setSource(candidate.source);
    setAgencyName(candidate.agency_name ?? "");
  }, [candidate, isDirty]);

  const handleSave = () => {
    updateCandidate.mutate(
      {
        expected_salary: expectedSalary ? Number(expectedSalary) : undefined,
        notice_period: noticePeriod ?? undefined,
        source: source ?? undefined,
        agency_name: source === "agency" ? agencyName || undefined : undefined,
      },
      { onSuccess: () => setIsDirty(false) }
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Candidate info</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-xs text-muted-foreground">
          Employer, title, and location are Owner-only Identity Vault fields — edit them from the
          project&apos;s Identity Vault tab.
        </p>

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

        <Field label="Notice period">
          <PillToggleGroup
            options={NOTICE_PERIOD_OPTIONS}
            value={noticePeriod}
            onChange={(value) => {
              setNoticePeriod(value);
              setIsDirty(true);
            }}
          />
        </Field>

        <Field label="Source of hire">
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

        <div className="flex justify-end">
          <Button size="sm" onClick={handleSave} disabled={!isDirty || updateCandidate.isPending}>
            {updateCandidate.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
