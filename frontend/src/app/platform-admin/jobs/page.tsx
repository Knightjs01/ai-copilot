"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Briefcase } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { JobRow } from "@/components/platform-admin/job-row";
import { useAdminJobs } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import type { ShadowJobStatus } from "@/lib/types";

type StatusFilter = ShadowJobStatus | "all";

const FILTERS: { value: StatusFilter; label: string }[] = [
  { value: "pending_review", label: "Pending review" },
  { value: "all", label: "All" },
  { value: "published", label: "Published" },
  { value: "closed", label: "Closed" },
  { value: "draft", label: "Draft" },
];

const PAGE_SIZE = 25;

export default function PlatformAdminJobsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
  const initialSearch = searchParams.get("search") ?? "";
  const [filter, setFilter] = React.useState<StatusFilter>(initialSearch ? "all" : "pending_review");
  const [search, setSearch] = React.useState(initialSearch);
  const [page, setPage] = React.useState(1);
  const { data, isLoading } = useAdminJobs(filter, undefined, {
    search,
    page,
    pageSize: PAGE_SIZE,
  });
  const jobs = data?.items ?? [];
  const total = data?.total ?? 0;
  const hasNextPage = page * PAGE_SIZE < total;

  React.useEffect(() => {
    if (authLoading) return;
    if (!admin) router.push("/platform-admin/login");
    else if (!hasPermission("jobs.view")) router.push("/platform-admin");
  }, [authLoading, admin, hasPermission, router]);

  React.useEffect(() => {
    setPage(1);
  }, [filter, search]);

  if (authLoading || !admin || !hasPermission("jobs.view")) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

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
          placeholder="Search jobs by title…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="sm:w-64"
        />
      </div>

      {!isLoading && (
        <p className="text-xs text-muted-foreground">
          Showing {jobs.length === 0 ? 0 : (page - 1) * PAGE_SIZE + 1}–
          {(page - 1) * PAGE_SIZE + jobs.length} of {total} jobs
        </p>
      )}

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && jobs.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <Briefcase className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No jobs match this filter.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && jobs.length > 0 && (
        <div className="flex flex-col gap-3">
          {jobs.map((job) => (
            <JobRow key={job.id} job={job} />
          ))}
        </div>
      )}

      {!isLoading && total > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </Button>
          <span className="text-xs text-muted-foreground">Page {page}</span>
          <Button
            variant="secondary"
            size="sm"
            disabled={!hasNextPage}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
