"use client";

import * as React from "react";
import Image from "next/image";
import { BadgeCheck, Calendar, Globe, MapPin } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { API_URL } from "@/lib/api-client";
import { COMPANY_SIZE_LABEL } from "@/lib/status-display";
import type { CompanyProfile, ContentItem } from "@/lib/types";

type Tab = "overview" | "culture" | "benefits" | "hiring-process";

const TAB_OPTIONS: { value: Tab; label: string }[] = [
  { value: "overview", label: "Overview" },
  { value: "culture", label: "Culture" },
  { value: "benefits", label: "Benefits" },
  { value: "hiring-process", label: "Hiring Process" },
];

function ContentItemGrid({ items }: { items: ContentItem[] }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {items.map((item) => (
        <div key={item.title} className="rounded-xl border border-border bg-secondary/20 p-4">
          <h3 className="text-sm font-semibold text-foreground">{item.title}</h3>
          <p className="mt-1 text-sm text-muted-foreground">{item.body}</p>
        </div>
      ))}
    </div>
  );
}

// Shared between the real public /companies/{slug} page, the wizard's "preview as candidate"
// step, and the platform-admin review dialog — all three should render byte-for-byte the same
// way, since they're all showing the same underlying shape (either a live snapshot or a draft).
// Relies entirely on semantic tokens (bg-secondary/text-foreground/border-border), never a
// hardcoded color, so it renders correctly whether the parent scope is the dark Shadow theme or
// the light ATS theme. Tabs are a plain PillToggleGroup switch, not a new Tabs primitive -- no
// such component exists elsewhere in this codebase, and this matches the brand exactly as-is.
export function CompanyProfilePreview({ company }: { company: CompanyProfile }) {
  const [tab, setTab] = React.useState<Tab>("overview");

  const hasCulture = !!company.culture;
  const hasBenefits = company.benefits.length > 0;
  const hasHiringProcess = !!company.hiring_process_overview;
  const availableTabs = TAB_OPTIONS.filter((t) => {
    if (t.value === "culture") return hasCulture;
    if (t.value === "benefits") return hasBenefits;
    if (t.value === "hiring-process") return hasHiringProcess;
    return true;
  });

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

      <div className="flex items-start gap-4">
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
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
              {company.name}
            </h1>
            {company.is_verified_employer && (
              <Badge variant="gold">
                <BadgeCheck className="h-3.5 w-3.5" />
                Verified
              </Badge>
            )}
          </div>
          {company.tagline && (
            <p className="text-sm text-muted-foreground">{company.tagline}</p>
          )}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
            {company.headquarters && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" />
                {company.headquarters}
              </span>
            )}
            {company.founded_year && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                Founded {company.founded_year}
              </span>
            )}
            {company.website && (
              <span className="flex items-center gap-1">
                <Globe className="h-3.5 w-3.5" />
                {company.website}
              </span>
            )}
          </div>
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

      {availableTabs.length > 1 && (
        <PillToggleGroup options={availableTabs} value={tab} onChange={setTab} />
      )}

      {tab === "overview" && (
        <div className="flex flex-col gap-4">
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
          {company.values.length > 0 && (
            <Card>
              <CardContent className="flex flex-col gap-3 py-5">
                <h2 className="text-sm font-semibold text-foreground">Our values</h2>
                <ContentItemGrid items={company.values} />
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {tab === "culture" && hasCulture && (
        <Card>
          <CardContent className="flex flex-col gap-2 py-5">
            <h2 className="text-sm font-semibold text-foreground">Culture</h2>
            <p className="whitespace-pre-line text-sm text-muted-foreground">{company.culture}</p>
          </CardContent>
        </Card>
      )}

      {tab === "benefits" && hasBenefits && (
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

      {tab === "hiring-process" && hasHiringProcess && (
        <Card>
          <CardContent className="flex flex-col gap-2 py-5">
            <h2 className="text-sm font-semibold text-foreground">Hiring process</h2>
            <p className="whitespace-pre-line text-sm text-muted-foreground">
              {company.hiring_process_overview}
            </p>
          </CardContent>
        </Card>
      )}

      {company.looking_for.length > 0 && (
        <Card>
          <CardContent className="flex flex-col gap-3 py-5">
            <h2 className="text-sm font-semibold text-foreground">What we look for</h2>
            <div className="flex flex-wrap gap-2">
              {company.looking_for.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-brand/10 px-2.5 py-1 text-xs font-medium text-brand"
                >
                  {tag}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {company.hiring_highlights.length > 0 && (
        <Card>
          <CardContent className="flex flex-col gap-3 py-5">
            <h2 className="text-sm font-semibold text-foreground">Hiring highlights</h2>
            <ContentItemGrid items={company.hiring_highlights} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
