"use client";

import { useParams } from "next/navigation";
import { Building2 } from "lucide-react";

import { CompanyProfilePreview } from "@/components/company/company-profile-preview";
import { ShadowAppShell } from "@/components/shadow/shadow-app-shell";
import { Spinner } from "@/components/ui/spinner";
import { useCompanyProfile } from "@/lib/queries/company";

export default function CompanyProfilePage() {
  const params = useParams<{ slug: string }>();
  const { data: company, isLoading } = useCompanyProfile(params.slug);

  return (
    <ShadowAppShell mainClassName="max-w-3xl">
      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && !company && (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
          <Building2 className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm font-medium text-foreground">Company not found</p>
          <p className="max-w-xs text-sm text-muted-foreground">
            This company doesn&apos;t have a public profile right now.
          </p>
        </div>
      )}

      {company && <CompanyProfilePreview company={company} />}
    </ShadowAppShell>
  );
}
