"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Briefcase } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
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

export default function PlatformAdminJobsPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
  const [filter, setFilter] = React.useState<StatusFilter>("pending_review");
  const { data: jobs, isLoading } = useAdminJobs(filter);

  React.useEffect(() => {
    if (authLoading) return;
    if (!admin) router.push("/platform-admin/login");
    else if (!hasPermission("jobs.view")) router.push("/platform-admin");
  }, [authLoading, admin, hasPermission, router]);

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

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && jobs?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <Briefcase className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No jobs match this filter.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && jobs && jobs.length > 0 && (
        <div className="flex flex-col gap-3">
          {jobs.map((job) => (
            <JobRow key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}
