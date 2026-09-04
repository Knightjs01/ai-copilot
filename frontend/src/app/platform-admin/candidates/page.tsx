"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { UserRound } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { useAdminCandidates } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { VERIFICATION_STATUS_LABEL, VERIFICATION_STATUS_VARIANT } from "@/lib/status-display";
import type { AdminCandidateSummary, VerificationStatus } from "@/lib/types";

type StatusFilter = VerificationStatus | "all";

const FILTERS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "unverified", label: "Unverified" },
  { value: "pending", label: "Pending" },
  { value: "verified", label: "Verified" },
];

function CandidateRow({ candidate }: { candidate: AdminCandidateSummary }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-foreground">
              {candidate.callsign ?? "Not yet approved"}
            </h3>
            <Badge variant={VERIFICATION_STATUS_VARIANT[candidate.verification_status]}>
              {VERIFICATION_STATUS_LABEL[candidate.verification_status]}
            </Badge>
            <Badge variant="outline">{candidate.visibility}</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {candidate.headline ?? "No headline yet"}
            {candidate.seniority ? ` · ${candidate.seniority}` : ""}
            {" · created "}
            {new Date(candidate.created_at).toLocaleDateString()}
          </p>
        </div>

        <Link
          href={`/platform-admin/candidates/${candidate.id}`}
          className="shrink-0 text-sm font-medium text-brand hover:underline"
        >
          View details →
        </Link>
      </CardContent>
    </Card>
  );
}

export default function PlatformAdminCandidatesPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
  const [filter, setFilter] = React.useState<StatusFilter>("all");
  const [search, setSearch] = React.useState("");
  const { data: candidates, isLoading } = useAdminCandidates(filter);

  React.useEffect(() => {
    if (authLoading) return;
    if (!admin) router.push("/platform-admin/login");
    else if (!hasPermission("candidates.view")) router.push("/platform-admin");
  }, [authLoading, admin, hasPermission, router]);

  if (authLoading || !admin || !hasPermission("candidates.view")) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  const filtered = (candidates ?? []).filter((c) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      (c.callsign ?? "").toLowerCase().includes(q) ||
      (c.headline ?? "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setFilter(f.value)}
              className={
                f.value === filter
                  ? "rounded-full bg-foreground px-3 py-1.5 text-xs font-medium text-background"
                  : "rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
              }
            >
              {f.label}
            </button>
          ))}
        </div>
        <Input
          placeholder="Search callsign or headline…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="sm:w-64"
        />
      </div>

      {!isLoading && candidates && (
        <p className="text-xs text-muted-foreground">
          Showing {filtered.length} of {candidates.length} candidates
        </p>
      )}

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && filtered.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <UserRound className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No candidates match this filter.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && filtered.length > 0 && (
        <div className="flex flex-col gap-3">
          {filtered.map((candidate) => (
            <CandidateRow key={candidate.id} candidate={candidate} />
          ))}
        </div>
      )}
    </div>
  );
}
