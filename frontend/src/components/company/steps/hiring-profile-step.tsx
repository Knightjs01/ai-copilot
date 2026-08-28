"use client";

import { ContentItemListEditor } from "@/components/company/content-item-list-editor";
import { Field } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import type { ContentItem } from "@/lib/types";

interface HiringProfileStepProps {
  hiringProcessOverview: string;
  onHiringProcessOverviewChange: (value: string) => void;
  hiringHighlights: ContentItem[];
  onHiringHighlightsChange: (items: ContentItem[]) => void;
}

export function HiringProfileStep({
  hiringProcessOverview,
  onHiringProcessOverviewChange,
  hiringHighlights,
  onHiringHighlightsChange,
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
      <Field label="Hiring highlights">
        <ContentItemListEditor
          items={hiringHighlights}
          onChange={onHiringHighlightsChange}
          addLabel="Add a highlight"
        />
      </Field>
    </div>
  );
}
