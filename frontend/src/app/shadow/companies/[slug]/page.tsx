"use client";

import { useParams } from "next/navigation";
import { Building2 } from "lucide-react";

import { ShadowTopNav } from "@/components/shadow/shadow-top-nav";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useCompanyProfile } from "@/lib/queries/company";
import { COMPANY_SIZE_LABEL } from "@/lib/status-display";
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

        {company && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
                {company.name}
              </h1>
              <div className="flex flex-wrap items-center gap-2">
                {company.size && (
                  <span className="rounded-full border border-border bg-secondary/40 px-2.5 py-0.5 text-xs text-foreground/80">
                    {COMPANY_SIZE_LABEL[company.size]}
                  </span>
                )}
                {company.industry.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full border border-border bg-secondary/40 px-2.5 py-0.5 text-xs text-foreground/80"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {company.description && (
              <Card>
                <CardContent className="flex flex-col gap-2 py-5">
                  <h2 className="text-sm font-semibold text-foreground">About</h2>
                  <p className="whitespace-pre-line text-sm text-muted-foreground">
                    {company.description}
                  </p>
                </CardContent>
              </Card>
            )}

            {company.culture && (
              <Card>
                <CardContent className="flex flex-col gap-2 py-5">
                  <h2 className="text-sm font-semibold text-foreground">Culture</h2>
                  <p className="whitespace-pre-line text-sm text-muted-foreground">
                    {company.culture}
                  </p>
                </CardContent>
              </Card>
            )}

            {company.benefits.length > 0 && (
              <Card>
                <CardContent className="flex flex-col gap-3 py-5">
                  <h2 className="text-sm font-semibold text-foreground">Benefits</h2>
                  <div className="flex flex-wrap gap-2">
                    {company.benefits.map((benefit) => (
                      <span
                        key={benefit}
                        className="rounded-full border border-border bg-secondary/40 px-2.5 py-1 text-xs text-foreground/80"
                      >
                        {benefit}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
