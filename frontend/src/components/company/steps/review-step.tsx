"use client";

import { CompanyProfilePreview } from "@/components/company/company-profile-preview";
import { CompanyStatusStrip } from "@/components/company/company-status-strip";
import { Spinner } from "@/components/ui/spinner";
import { usePreviewCompanyProfile } from "@/lib/queries/company";
import type { CompanyProfileStatus } from "@/lib/types";

export function ReviewStep({ profileStatus }: { profileStatus: CompanyProfileStatus }) {
  const { data: preview, isLoading } = usePreviewCompanyProfile();

  return (
    <div className="flex flex-col gap-5">
      <CompanyStatusStrip status={profileStatus} />
      <p className="text-sm text-muted-foreground">
        This is exactly what candidates will see once your profile is approved.
      </p>
      {isLoading && (
        <div className="flex justify-center py-10">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}
      {preview && <CompanyProfilePreview company={preview} />}
    </div>
  );
}
