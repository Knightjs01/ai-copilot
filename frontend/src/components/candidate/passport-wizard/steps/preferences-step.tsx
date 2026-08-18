"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
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

interface PreferencesStepProps {
  location: string;
  onLocationChange: (value: string) => void;
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
  location,
  onLocationChange,
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
  return (
    <Card>
      <CardHeader>
        <CardTitle>Preferences</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Field label="Location" htmlFor="location">
          <Input id="location" value={location} onChange={(e) => onLocationChange(e.target.value)} />
        </Field>
        <Field label="Remote preference">
          <PillToggleGroup
            options={REMOTE_PREFERENCE_OPTIONS}
            value={remotePreference}
            onChange={onRemotePreferenceChange}
          />
        </Field>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Minimum salary" htmlFor="salaryMin">
            <Input
              id="salaryMin"
              type="number"
              min={0}
              value={salaryMin}
              onChange={(e) => onSalaryMinChange(e.target.value)}
            />
          </Field>
          <Field label="Maximum salary" htmlFor="salaryMax">
            <Input
              id="salaryMax"
              type="number"
              min={0}
              value={salaryMax}
              onChange={(e) => onSalaryMaxChange(e.target.value)}
            />
          </Field>
        </div>
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
