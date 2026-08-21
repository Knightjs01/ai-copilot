"use client";

import Image from "next/image";

import { Dropzone } from "@/components/ui/dropzone";
import { Field } from "@/components/ui/field";
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
  size: CompanySizeBand | null;
  onSizeChange: (value: CompanySizeBand) => void;
  industry: string[];
  onIndustryChange: (values: string[]) => void;
}

export function IdentityStep({
  logoUrl,
  onUploadLogo,
  isUploadingLogo,
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
      <Field label="Company size">
        <PillToggleGroup options={SIZE_OPTIONS} value={size} onChange={onSizeChange} />
      </Field>
      <Field label="Industry" htmlFor="industry">
        <TagInput id="industry" values={industry} onValuesChange={onIndustryChange} placeholder="Add an industry…" />
      </Field>
    </div>
  );
}
