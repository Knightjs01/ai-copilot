"use client";

import { Field } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";

interface HiringProfileStepProps {
  hiringProcessOverview: string;
  onHiringProcessOverviewChange: (value: string) => void;
}

export function HiringProfileStep({
  hiringProcessOverview,
  onHiringProcessOverviewChange,
}: HiringProfileStepProps) {
  return (
    <div className="flex flex-col gap-5">
      <Field label="Hiring process" htmlFor="hiringProcessOverview">
        <Textarea
          id="hiringProcessOverview"
          rows={5}
          placeholder="What can candidates expect? e.g. Screen call, two interviews, offer."
          value={hiringProcessOverview}
          onChange={(e) => onHiringProcessOverviewChange(e.target.value)}
        />
      </Field>
    </div>
  );
}
