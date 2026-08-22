"use client";

import Link from "next/link";
import { ArrowRight, Search, ShieldAlert, UsersRound } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";

export default function TalentHubPage() {
  const { hasPermission } = useAuth();
  const canViewTalentPool = hasPermission("talent_pool.view");
  const canSearchCandidates = hasPermission("shadow_candidates.search");

  if (!canViewTalentPool && !canSearchCandidates) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Talent isn&apos;t available on your role</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Talent</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          People you may want to hire now or in the future — distinct from Candidates, who are
          currently interacting with your hiring process.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {canViewTalentPool && (
          <Link href="/talent-pool">
            <Card className="h-full transition-colors hover:border-brand">
              <CardHeader className="flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <UsersRound className="h-4 w-4 text-brand" />
                  Talent Pool
                </CardTitle>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Candidates who&apos;ve granted your company permission to stay on file for
                  future roles.
                </p>
              </CardContent>
            </Card>
          </Link>
        )}

        {canSearchCandidates && (
          <Link href="/search-candidates">
            <Card className="h-full transition-colors hover:border-brand">
              <CardHeader className="flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-4 w-4 text-brand" />
                  Search Candidates
                </CardTitle>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Find AI-matched candidates from the discoverable Shadow pool for a specific
                  role.
                </p>
              </CardContent>
            </Card>
          </Link>
        )}
      </div>
    </div>
  );
}
