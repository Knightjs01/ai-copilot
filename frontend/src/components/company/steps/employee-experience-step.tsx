"use client";

import { ContentItemListEditor } from "@/components/company/content-item-list-editor";
import { Field } from "@/components/ui/field";
import { TagInput } from "@/components/ui/tag-input";
import type { ContentItem } from "@/lib/types";

interface EmployeeExperienceStepProps {
  values: ContentItem[];
  onValuesChange: (items: ContentItem[]) => void;
  lookingFor: string[];
  onLookingForChange: (values: string[]) => void;
  benefits: string[];
  onBenefitsChange: (values: string[]) => void;
}

export function EmployeeExperienceStep({
  values,
  onValuesChange,
  lookingFor,
  onLookingForChange,
  benefits,
  onBenefitsChange,
}: EmployeeExperienceStepProps) {
  return (
    <div className="flex flex-col gap-5">
      <Field label="Our values">
        <ContentItemListEditor items={values} onChange={onValuesChange} addLabel="Add a value" />
      </Field>
      <Field label="What we look for" htmlFor="looking-for">
        <TagInput
          id="looking-for"
          values={lookingFor}
          onValuesChange={onLookingForChange}
          placeholder="e.g. Problem solvers…"
        />
      </Field>
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
