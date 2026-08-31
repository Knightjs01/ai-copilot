"use client";

import { Building2 } from "lucide-react";

import { CompanyBoardCard } from "@/components/shadow/company-board-card";
import { EmptyState } from "@/components/shadow/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { useCompanyBoard } from "@/lib/queries/company";

// Same real GET /companies/board data as the Home page's "Explore companies" preview -- just its
// own full page with a higher limit, reachable from the sidebar instead of only a Home preview.
export default function ShadowCompaniesPage() {
  const { data: companies, isLoading } = useCompanyBoard(24);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Explore companies
        </h1>
        <p className="text-sm text-muted-foreground">
          Organisations actively building and investing in talent on Phantom.
        </p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      ) : companies && companies.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {companies.map((company) => (
            <CompanyBoardCard key={company.slug} company={company} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Building2}
          title="No companies live yet"
          description="Check back soon as more companies join Phantom."
        />
      )}
    </div>
  );
}
