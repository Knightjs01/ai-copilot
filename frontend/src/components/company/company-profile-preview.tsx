import Image from "next/image";

import { Card, CardContent } from "@/components/ui/card";
import { API_URL } from "@/lib/api-client";
import { COMPANY_SIZE_LABEL } from "@/lib/status-display";
import type { CompanyProfile } from "@/lib/types";

// Shared between the real public /companies/{slug} page, the wizard's "preview as candidate"
// step, and the platform-admin review dialog — all three should render byte-for-byte the same
// way, since they're all showing the same underlying shape (either a live snapshot or a draft).
// Relies entirely on semantic tokens (bg-secondary/text-foreground/border-border), never a
// hardcoded color, so it renders correctly whether the parent scope is the dark Shadow theme or
// the light ATS theme.
export function CompanyProfilePreview({ company }: { company: CompanyProfile }) {
  return (
    <div className="flex flex-col gap-6">
      {company.cover_image_url && (
        <div className="relative h-40 w-full overflow-hidden rounded-2xl border border-border sm:h-56">
          <Image
            src={`${API_URL}${company.cover_image_url}`}
            alt=""
            fill
            className="object-cover"
            unoptimized
          />
        </div>
      )}

      <div className="flex items-center gap-4">
        {company.logo_url && (
          <div className="relative h-14 w-14 shrink-0 overflow-hidden rounded-xl border border-border bg-card">
            <Image
              src={`${API_URL}${company.logo_url}`}
              alt={`${company.name} logo`}
              fill
              className="object-contain"
              unoptimized
            />
          </div>
        )}
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

      {company.hiring_process_overview && (
        <Card>
          <CardContent className="flex flex-col gap-2 py-5">
            <h2 className="text-sm font-semibold text-foreground">Hiring process</h2>
            <p className="whitespace-pre-line text-sm text-muted-foreground">
              {company.hiring_process_overview}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
