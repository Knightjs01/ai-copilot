import Image from "next/image";
import Link from "next/link";
import { BadgeCheck, Building2, MapPin, Users } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { API_URL } from "@/lib/api-client";
import type { CompanyBoardCard as CompanyBoardCardData } from "@/lib/types";

// Same verified-badge/logo-image conventions as company-profile-preview.tsx (the single-company
// detail page) -- kept visually consistent even though this is a much smaller card. The
// cover-image header falls back to a soft brand gradient panel when a company hasn't uploaded
// one -- never a placeholder stock photo standing in for real content.
export function CompanyBoardCard({ company }: { company: CompanyBoardCardData }) {
  return (
    <Link href={`/shadow/companies/${company.slug}`}>
      <Card className="h-full overflow-hidden transition-colors hover:border-brand/40">
        <div className="relative h-16 w-full">
          {company.cover_image_url ? (
            <Image
              src={`${API_URL}${company.cover_image_url}`}
              alt=""
              fill
              className="object-cover"
              unoptimized
            />
          ) : (
            <div className="h-full w-full bg-gradient-to-br from-brand/10 to-electric/10" />
          )}
          <div className="absolute -bottom-4 left-4 flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-lg border-2 border-card bg-secondary/60">
            {company.logo_url ? (
              <Image
                src={`${API_URL}${company.logo_url}`}
                alt={`${company.name} logo`}
                fill
                className="object-contain"
                unoptimized
              />
            ) : (
              <Building2 className="h-4.5 w-4.5 text-muted-foreground" />
            )}
          </div>
        </div>
        <CardContent className="flex flex-col gap-3 p-4 pt-6">
          <div className="flex min-w-0 flex-col">
            <div className="flex items-center gap-1.5">
              <p className="truncate text-sm font-semibold text-foreground">{company.name}</p>
              {company.is_verified_employer && (
                <BadgeCheck className="h-3.5 w-3.5 shrink-0 text-gold" />
              )}
            </div>
            {company.tagline && (
              <p className="truncate text-xs text-muted-foreground">{company.tagline}</p>
            )}
          </div>

          {company.industry.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {company.industry.slice(0, 2).map((tag) => (
                <Badge key={tag} variant="neutral">
                  {tag}
                </Badge>
              ))}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
            {company.headquarters && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" />
                {company.headquarters}
              </span>
            )}
            {company.employee_count != null && (
              <span className="flex items-center gap-1">
                <Users className="h-3.5 w-3.5" />
                {company.employee_count.toLocaleString()} employees
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
