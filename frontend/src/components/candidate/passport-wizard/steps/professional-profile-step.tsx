"use client";

import { Plus, Sparkles, Trash2 } from "lucide-react";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { TagInput } from "@/components/ui/tag-input";
import { Textarea } from "@/components/ui/textarea";
import type { CareerEntryInput } from "@/lib/types";

function AiFieldBadge({
  field,
  aiSuggestedFields,
}: {
  field: string;
  aiSuggestedFields: string[] | null;
}) {
  if (aiSuggestedFields === null) return null;
  const suggested = aiSuggestedFields.includes(field);
  return (
    <Badge variant={suggested ? "info" : "success"} className="ml-2 align-middle">
      {suggested ? "✦ Suggested by Phantom AI" : "✓ Extracted from your CV"}
    </Badge>
  );
}

interface ProfessionalProfileStepProps {
  headline: string;
  onHeadlineChange: (value: string) => void;
  seniority: string;
  onSeniorityChange: (value: string) => void;
  yearsExperience: string;
  onYearsExperienceChange: (value: string) => void;
  summary: string;
  onSummaryChange: (value: string) => void;
  skills: string[];
  onSkillsChange: (value: string[]) => void;
  industries: string[];
  onIndustriesChange: (value: string[]) => void;
  aiSuggestedFields: string[] | null;

  careerEntries: CareerEntryInput[];
  onUpdateEntry: (index: number, patch: Partial<CareerEntryInput>) => void;
  onRemoveEntry: (index: number) => void;
  onAddEntry: () => void;

  // AI co-pilot — always a suggestion to Apply or Dismiss, never a silent overwrite.
  onRequestSummarySuggestion: () => void;
  isSuggestingSummary: boolean;
  summarySuggestion: string | null;
  summarySuggestionError: string | null;
  onApplySummarySuggestion: () => void;
  onDismissSummarySuggestion: () => void;

  onRequestSkillsSuggestion: () => void;
  isSuggestingSkills: boolean;
  skillsSuggestions: string[] | null;
  skillsSuggestionError: string | null;

  onRequestIndustriesSuggestion: () => void;
  isSuggestingIndustries: boolean;
  industriesSuggestions: string[] | null;
  industriesSuggestionError: string | null;
}

export function ProfessionalProfileStep({
  headline,
  onHeadlineChange,
  seniority,
  onSeniorityChange,
  yearsExperience,
  onYearsExperienceChange,
  summary,
  onSummaryChange,
  skills,
  onSkillsChange,
  industries,
  onIndustriesChange,
  aiSuggestedFields,
  careerEntries,
  onUpdateEntry,
  onRemoveEntry,
  onAddEntry,
  onRequestSummarySuggestion,
  isSuggestingSummary,
  summarySuggestion,
  summarySuggestionError,
  onApplySummarySuggestion,
  onDismissSummarySuggestion,
  onRequestSkillsSuggestion,
  isSuggestingSkills,
  skillsSuggestions,
  skillsSuggestionError,
  onRequestIndustriesSuggestion,
  isSuggestingIndustries,
  industriesSuggestions,
  industriesSuggestionError,
}: ProfessionalProfileStepProps) {
  return (
    <Accordion
      type="multiple"
      defaultValue={["core", "skills", "career"]}
      className="flex flex-col gap-3"
    >
      <AccordionItem value="core" className="rounded-2xl border border-border bg-card px-4">
        <AccordionTrigger>Core profile</AccordionTrigger>
        <AccordionContent>
          <div className="flex flex-col gap-4">
            <Field label="Headline" htmlFor="headline">
              <Input
                id="headline"
                placeholder="e.g. Senior Product Leader"
                value={headline}
                onChange={(e) => onHeadlineChange(e.target.value)}
              />
            </Field>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Seniority" htmlFor="seniority">
                <Input
                  id="seniority"
                  placeholder="e.g. Senior"
                  value={seniority}
                  onChange={(e) => onSeniorityChange(e.target.value)}
                />
              </Field>
              <Field label="Years of experience" htmlFor="yearsExperience">
                <Input
                  id="yearsExperience"
                  type="number"
                  min={0}
                  value={yearsExperience}
                  onChange={(e) => onYearsExperienceChange(e.target.value)}
                />
              </Field>
            </div>
            <Field label="Summary" htmlFor="summary">
              <Textarea id="summary" value={summary} onChange={(e) => onSummaryChange(e.target.value)} />
            </Field>
            <div className="flex flex-col gap-2">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="self-start"
                onClick={onRequestSummarySuggestion}
                disabled={isSuggestingSummary || !summary.trim()}
              >
                <Sparkles className="h-3.5 w-3.5" />
                {isSuggestingSummary ? "Thinking…" : "Improve my summary"}
              </Button>
              {summarySuggestionError && (
                <p className="text-xs font-medium text-danger">{summarySuggestionError}</p>
              )}
              {summarySuggestion && (
                <div className="flex flex-col gap-2 rounded-xl border border-info/20 bg-info/5 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-info">
                    Phantom AI suggests
                  </p>
                  <p className="text-sm text-foreground">{summarySuggestion}</p>
                  <div className="flex gap-2">
                    <Button type="button" size="sm" variant="brand" onClick={onApplySummarySuggestion}>
                      Apply
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      onClick={onDismissSummarySuggestion}
                    >
                      Dismiss
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="skills" className="rounded-2xl border border-border bg-card px-4">
        <AccordionTrigger>Skills & industries</AccordionTrigger>
        <AccordionContent>
          <div className="flex flex-col gap-5">
            <Field
              label={
                <>
                  Skills
                  <AiFieldBadge field="skills" aiSuggestedFields={aiSuggestedFields} />
                </>
              }
              htmlFor="skills"
            >
              <TagInput
                id="skills"
                values={skills}
                onValuesChange={onSkillsChange}
                placeholder="Add your own and press Enter"
                suggestions={skillsSuggestions ?? undefined}
                onRequestSuggestions={onRequestSkillsSuggestion}
                isSuggesting={isSuggestingSkills}
                suggestionsButtonLabel="Suggest skills"
              />
              {skillsSuggestionError && (
                <p className="text-xs font-medium text-danger">{skillsSuggestionError}</p>
              )}
            </Field>
            <Field
              label={
                <>
                  Industries
                  <AiFieldBadge field="industries" aiSuggestedFields={aiSuggestedFields} />
                </>
              }
              htmlFor="industries"
            >
              <TagInput
                id="industries"
                values={industries}
                onValuesChange={onIndustriesChange}
                placeholder="Type an industry and press Enter"
                suggestions={industriesSuggestions ?? undefined}
                onRequestSuggestions={onRequestIndustriesSuggestion}
                isSuggesting={isSuggestingIndustries}
                suggestionsButtonLabel="Suggest industries"
              />
              {industriesSuggestionError && (
                <p className="text-xs font-medium text-danger">{industriesSuggestionError}</p>
              )}
            </Field>
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="career" className="rounded-2xl border border-border bg-card px-4">
        <AccordionTrigger>Career history</AccordionTrigger>
        <AccordionContent>
          <div className="flex flex-col gap-4">
            {careerEntries.map((entry, index) => (
              <div key={index} className="flex flex-col gap-3 rounded-xl border border-border p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="grid flex-1 grid-cols-2 gap-3">
                    <Field label="Title" htmlFor={`title-${index}`}>
                      <Input
                        id={`title-${index}`}
                        value={entry.title}
                        onChange={(e) => onUpdateEntry(index, { title: e.target.value })}
                      />
                    </Field>
                    <Field label="Real employer" htmlFor={`company-${index}`}>
                      <Input
                        id={`company-${index}`}
                        placeholder="Never shown until you approve a reveal"
                        value={entry.company_name}
                        onChange={(e) => onUpdateEntry(index, { company_name: e.target.value })}
                      />
                    </Field>
                  </div>
                  <button
                    type="button"
                    onClick={() => onRemoveEntry(index)}
                    className="mt-6 rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-danger"
                    aria-label="Remove entry"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                <Field
                  label={
                    <>
                      Anonymized employer
                      <AiFieldBadge
                        field="company_name_anonymized"
                        aiSuggestedFields={aiSuggestedFields}
                      />
                    </>
                  }
                  htmlFor={`anon-${index}`}
                >
                  <Input
                    id={`anon-${index}`}
                    placeholder='e.g. "Global Payments Platform" instead of "Stripe": this is what recruiters see'
                    value={entry.company_name_anonymized}
                    onChange={(e) =>
                      onUpdateEntry(index, { company_name_anonymized: e.target.value })
                    }
                  />
                </Field>
                <Field label="What you did" htmlFor={`resp-${index}`}>
                  <Textarea
                    id={`resp-${index}`}
                    value={entry.responsibilities ?? ""}
                    onChange={(e) => onUpdateEntry(index, { responsibilities: e.target.value })}
                  />
                </Field>
                <Field label="Achievements" htmlFor={`achievements-${index}`}>
                  <Input
                    id={`achievements-${index}`}
                    placeholder="Comma-separated"
                    value={(entry.achievements ?? []).join(", ")}
                    onChange={(e) =>
                      onUpdateEntry(index, {
                        achievements: e.target.value
                          .split(",")
                          .map((s) => s.trim())
                          .filter(Boolean),
                      })
                    }
                  />
                </Field>
                <label className="flex items-center gap-2 text-sm text-muted-foreground">
                  <input
                    type="checkbox"
                    className="accent-brand"
                    checked={entry.is_current}
                    onChange={(e) => onUpdateEntry(index, { is_current: e.target.checked })}
                  />
                  I currently work here
                </label>
              </div>
            ))}
            {careerEntries.length === 0 && (
              <p className="text-sm text-muted-foreground">No roles added yet.</p>
            )}
            <Button type="button" variant="secondary" size="sm" className="self-start" onClick={onAddEntry}>
              <Plus className="h-4 w-4" /> Add role
            </Button>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
