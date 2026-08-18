"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { Slider } from "@/components/ui/slider";
import {
  CAREER_INTENT_LABEL,
  NOTICE_PERIOD_LABEL,
  REMOTE_PREFERENCE_LABEL,
} from "@/lib/status-display";
import type { CareerIntent, NoticePeriod, RemotePreference } from "@/lib/types";

const CAREER_INTENT_OPTIONS = (Object.keys(CAREER_INTENT_LABEL) as CareerIntent[]).map((value) => ({
  value,
  label: CAREER_INTENT_LABEL[value],
}));
const REMOTE_PREFERENCE_OPTIONS = (Object.keys(REMOTE_PREFERENCE_LABEL) as RemotePreference[]).map(
  (value) => ({ value, label: REMOTE_PREFERENCE_LABEL[value] })
);
const NOTICE_PERIOD_OPTIONS = (Object.keys(NOTICE_PERIOD_LABEL) as NoticePeriod[]).map((value) => ({
  value,
  label: NOTICE_PERIOD_LABEL[value],
}));

// Bounds and step for the visual slider only — the numeric inputs beside it still accept any
// value, so a salary outside this range is entered by typing, not dragging.
const SALARY_SLIDER_MIN = 0;
const SALARY_SLIDER_MAX = 300000;
const SALARY_SLIDER_STEP = 5000;

function formatSalary(value: number): string {
  return `£${value.toLocaleString("en-GB")}`;
}

interface PreferencesStepProps {
  remotePreference: RemotePreference | null;
  onRemotePreferenceChange: (value: RemotePreference) => void;
  salaryMin: string;
  onSalaryMinChange: (value: string) => void;
  salaryMax: string;
  onSalaryMaxChange: (value: string) => void;
  noticePeriod: NoticePeriod | null;
  onNoticePeriodChange: (value: NoticePeriod) => void;
  careerIntent: CareerIntent;
  onCareerIntentChange: (value: CareerIntent) => void;
}

export function PreferencesStep({
  remotePreference,
  onRemotePreferenceChange,
  salaryMin,
  onSalaryMinChange,
  salaryMax,
  onSalaryMaxChange,
  noticePeriod,
  onNoticePeriodChange,
  careerIntent,
  onCareerIntentChange,
}: PreferencesStepProps) {
  const minValue = Math.min(
    Math.max(Number(salaryMin) || SALARY_SLIDER_MIN, SALARY_SLIDER_MIN),
    SALARY_SLIDER_MAX
  );
  const maxValue = Math.min(
    Math.max(Number(salaryMax) || SALARY_SLIDER_MIN, SALARY_SLIDER_MIN),
    SALARY_SLIDER_MAX
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Preferences</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Field label="Remote preference">
          <PillToggleGroup
            options={REMOTE_PREFERENCE_OPTIONS}
            value={remotePreference}
            onChange={onRemotePreferenceChange}
          />
        </Field>
        <Field label="Salary expectations">
          <div className="flex flex-col gap-4 rounded-xl border border-border bg-background px-4 py-4">
            <div className="flex items-center justify-between text-sm font-medium text-foreground">
              <span>{formatSalary(minValue)}</span>
              <span className="text-muted-foreground">to</span>
              <span>{formatSalary(maxValue)}</span>
            </div>
            <Slider
              min={SALARY_SLIDER_MIN}
              max={SALARY_SLIDER_MAX}
              step={SALARY_SLIDER_STEP}
              value={[minValue, Math.max(maxValue, minValue)]}
              onValueChange={(next: number[]) => {
                const [nextMin, nextMax] = next;
                if (nextMin == null || nextMax == null) return;
                onSalaryMinChange(String(nextMin));
                onSalaryMaxChange(String(Math.max(nextMax, nextMin)));
              }}
            />
            <div className="grid grid-cols-2 gap-4">
              <Field label="Minimum" htmlFor="salaryMin">
                <Input
                  id="salaryMin"
                  type="number"
                  min={0}
                  value={salaryMin}
                  onChange={(e) => onSalaryMinChange(e.target.value)}
                />
              </Field>
              <Field label="Maximum" htmlFor="salaryMax">
                <Input
                  id="salaryMax"
                  type="number"
                  min={0}
                  value={salaryMax}
                  onChange={(e) => onSalaryMaxChange(e.target.value)}
                />
              </Field>
            </div>
          </div>
        </Field>
        <Field label="Notice period">
          <PillToggleGroup
            options={NOTICE_PERIOD_OPTIONS}
            value={noticePeriod}
            onChange={onNoticePeriodChange}
          />
        </Field>
        <Field label="Career intent">
          <PillToggleGroup
            options={CAREER_INTENT_OPTIONS}
            value={careerIntent}
            onChange={onCareerIntentChange}
          />
        </Field>
      </CardContent>
    </Card>
  );
}
