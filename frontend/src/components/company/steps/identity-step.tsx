"use client";

import Image from "next/image";

import { Dropzone } from "@/components/ui/dropzone";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { TagInput } from "@/components/ui/tag-input";
import { API_URL } from "@/lib/api-client";
import { COMPANY_SIZE_LABEL } from "@/lib/status-display";
import type { CompanySizeBand } from "@/lib/types";

const SIZE_OPTIONS = (Object.keys(COMPANY_SIZE_LABEL) as CompanySizeBand[]).map((value) => ({
  value,
  label: COMPANY_SIZE_LABEL[value],
}));

interface IdentityStepProps {
  logoUrl: string | null;
  onUploadLogo: (file: File) => void;
  isUploadingLogo: boolean;
  tagline: string;
  onTaglineChange: (value: string) => void;
  website: string;
  onWebsiteChange: (value: string) => void;
  foundedYear: string;
  onFoundedYearChange: (value: string) => void;
  headquarters: string;
  onHeadquartersChange: (value: string) => void;
  employeeCount: string;
  onEmployeeCountChange: (value: string) => void;
  size: CompanySizeBand | null;
  onSizeChange: (value: CompanySizeBand) => void;
  industry: string[];
  onIndustryChange: (values: string[]) => void;
}

export function IdentityStep({
  logoUrl,
  onUploadLogo,
  isUploadingLogo,
  tagline,
  onTaglineChange,
  website,
  onWebsiteChange,
  foundedYear,
  onFoundedYearChange,
  headquarters,
  onHeadquartersChange,
  employeeCount,
  onEmployeeCountChange,
  size,
  onSizeChange,
  industry,
  onIndustryChange,
}: IdentityStepProps) {
  return (
    <div className="flex flex-col gap-5">
      <Field label="Logo">
        <div className="flex items-center gap-4">
          {logoUrl && (
            <div className="relative h-14 w-14 shrink-0 overflow-hidden rounded-xl border border-border bg-card">
              <Image src={`${API_URL}${logoUrl}`} alt="" fill className="object-contain" unoptimized />
            </div>
          )}
          <Dropzone
            className="flex-1"
            accept="image/png,image/jpeg,image/webp"
            label="Upload a logo"
            hint="PNG, JPEG, or WebP, up to 5MB"
            currentFileName={logoUrl ? "Logo uploaded" : null}
            isUploading={isUploadingLogo}
            onFileSelected={onUploadLogo}
          />
        </div>
      </Field>
      <Field label="Tagline" htmlFor="tagline">
        <Input
          id="tagline"
          value={tagline}
          onChange={(e) => onTaglineChange(e.target.value)}
          placeholder="e.g. Backing exceptional teams building the future."
          maxLength={255}
        />
      </Field>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <Field label="Website" htmlFor="website">
          <Input
            id="website"
            value={website}
            onChange={(e) => onWebsiteChange(e.target.value)}
            placeholder="example.com"
            maxLength={255}
          />
        </Field>
        <Field label="Founded year" htmlFor="founded-year">
          <Input
            id="founded-year"
            type="number"
            value={foundedYear}
            onChange={(e) => onFoundedYearChange(e.target.value)}
            placeholder="2013"
            min={1800}
            max={2100}
          />
        </Field>
      </div>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <Field label="Headquarters" htmlFor="headquarters">
          <Input
            id="headquarters"
            value={headquarters}
            onChange={(e) => onHeadquartersChange(e.target.value)}
            placeholder="London, United Kingdom"
            maxLength={255}
          />
        </Field>
        <Field label="Employee count" htmlFor="employee-count">
          <Input
            id="employee-count"
            type="number"
            value={employeeCount}
            onChange={(e) => onEmployeeCountChange(e.target.value)}
            placeholder="84"
            min={0}
          />
        </Field>
      </div>
      <Field label="Company size">
        <PillToggleGroup options={SIZE_OPTIONS} value={size} onChange={onSizeChange} />
      </Field>
      <Field label="Industry" htmlFor="industry">
        <TagInput id="industry" values={industry} onValuesChange={onIndustryChange} placeholder="Add an industry…" />
      </Field>
    </div>
  );
}
