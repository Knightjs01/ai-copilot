"use client";

import { Field } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";

interface AboutStepProps {
  description: string;
  onDescriptionChange: (value: string) => void;
  culture: string;
  onCultureChange: (value: string) => void;
}

export function AboutStep({
  description,
  onDescriptionChange,
  culture,
  onCultureChange,
}: AboutStepProps) {
  return (
    <div className="flex flex-col gap-5">
      <Field label="About" htmlFor="description">
        <Textarea
          id="description"
          rows={5}
          placeholder="What does your company do?"
          value={description}
          onChange={(e) => onDescriptionChange(e.target.value)}
        />
      </Field>
      <Field label="Culture" htmlFor="culture">
        <Textarea
          id="culture"
          rows={5}
          placeholder="What's it like to work here?"
          value={culture}
          onChange={(e) => onCultureChange(e.target.value)}
        />
      </Field>
    </div>
  );
}
