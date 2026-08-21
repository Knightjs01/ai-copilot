"use client";

import { useParams } from "next/navigation";
import { Building2 } from "lucide-react";

import { CompanyProfilePreview } from "@/components/company/company-profile-preview";
import { ShadowTopNav } from "@/components/shadow/shadow-top-nav";
import { Spinner } from "@/components/ui/spinner";
import { useCompanyProfile } from "@/lib/queries/company";
import styles from "../../shadow-theme.module.css";

export default function CompanyProfilePage() {
  const params = useParams<{ slug: string }>();
  const { data: company, isLoading } = useCompanyProfile(params.slug);

  return (
    // ShadowTopNav + this outer bg-slate-50 gutter stay light, same pattern as every other
    // Shadow page — only <main> goes obsidian/blue.
    <div className="min-h-screen bg-slate-50">
      <ShadowTopNav />
      <main className={`${styles.shadowTheme} mx-auto max-w-3xl rounded-2xl px-6 py-10`}>
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
      </main>
    </div>
  );
}
