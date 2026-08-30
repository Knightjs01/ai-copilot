"use client";

import { MapPin, Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { TagInput } from "@/components/ui/tag-input";

// Dumb controlled toolbar -- the parent (search-candidates/page.tsx) owns every value via
// useState and passes it back down, mirroring shadow-board-toolbar.tsx's exact pattern. Location/
// seniority/minYearsExperience/skills are pre-scoring filters sent to the backend (see
// useCandidateSearch); previouslyEngagedOnly is a pure client-side filter over relationship_status
// already present on every fetched result, so it needs no query param at all.
export function CandidateSearchToolbar({
  location,
  onLocationChange,
  seniority,
  onSeniorityChange,
  minYearsExperience,
  onMinYearsExperienceChange,
  skills,
  onSkillsChange,
  previouslyEngagedOnly,
  onPreviouslyEngagedOnlyChange,
  resultCount,
}: {
  location: string;
  onLocationChange: (value: string) => void;
  seniority: string;
  onSeniorityChange: (value: string) => void;
  minYearsExperience: string;
  onMinYearsExperienceChange: (value: string) => void;
  skills: string[];
  onSkillsChange: (values: string[]) => void;
  previouslyEngagedOnly: boolean;
  onPreviouslyEngagedOnlyChange: (checked: boolean) => void;
  resultCount?: number;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="relative">
          <MapPin className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={location}
            onChange={(e) => onLocationChange(e.target.value)}
            placeholder="Location"
            className="pl-9"
          />
        </div>
        <Input
          value={seniority}
          onChange={(e) => onSeniorityChange(e.target.value)}
          placeholder="Seniority (e.g. Senior)"
        />
        <Input
          type="number"
          min={0}
          value={minYearsExperience}
          onChange={(e) => onMinYearsExperienceChange(e.target.value)}
          placeholder="Min years experience"
        />
        <div className="flex items-center gap-2 rounded-xl border border-border px-3 py-2">
          <Switch
            checked={previouslyEngagedOnly}
            onCheckedChange={onPreviouslyEngagedOnlyChange}
            aria-label="Previously engaged only"
          />
          <span className="text-sm text-foreground">Previously engaged only</span>
        </div>
      </div>

      <TagInput
        values={skills}
        onValuesChange={onSkillsChange}
        placeholder="Required skills — press Enter to add"
      />

      {resultCount != null && (
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Search className="h-3.5 w-3.5" />
          {resultCount} candidate{resultCount === 1 ? "" : "s"}
        </div>
      )}
    </div>
  );
}
