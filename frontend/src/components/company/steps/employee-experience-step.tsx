"use client";

import { Field } from "@/components/ui/field";
import { TagInput } from "@/components/ui/tag-input";

interface EmployeeExperienceStepProps {
  benefits: string[];
  onBenefitsChange: (values: string[]) => void;
}

export function EmployeeExperienceStep({
  benefits,
  onBenefitsChange,
}: EmployeeExperienceStepProps) {
  return (
    <div className="flex flex-col gap-5">
      <Field label="Benefits" htmlFor="benefits">
        <TagInput
          id="benefits"
          values={benefits}
          onValuesChange={onBenefitsChange}
          placeholder="Add a benefit…"
        />
      </Field>
    </div>
  );
}
