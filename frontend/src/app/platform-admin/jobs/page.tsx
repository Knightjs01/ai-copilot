"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Briefcase } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { useAdminJobs } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { formatSalary } from "@/lib/format";
import { SHADOW_JOB_STATUS_LABEL, SHADOW_JOB_STATUS_VARIANT } from "@/lib/status-display";
import type { AdminShadowJob, ShadowJobStatus } from "@/lib/types";

type StatusFilter = ShadowJobStatus | "all";

const FILTERS: { value: StatusFilter; label: string }[] = [
  { value: "pending_review", label: "Pending review" },
  { value: "all", label: "All" },
  { value: "published", label: "Published" },
  { value: "closed", label: "Closed" },
  { value: "draft", label: "Draft" },
];

function JobRow({ job }: { job: AdminShadowJob }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-foreground">{job.title}</h3>
            <Badge variant="outline">{job.company_name}</Badge>
            <Badge variant={SHADOW_JOB_STATUS_VARIANT[job.status]}>
              {SHADOW_JOB_STATUS_LABEL[job.status]}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {job.department ? `${job.department} · ` : ""}
            {job.location ?? "Remote/unspecified"}
            {job.salary_min || job.salary_max
              ? ` · ${formatSalary(job.salary_min, job.salary_max)}`
              : ""}
            {" · "}
            {job.applicant_count} applicant{job.applicant_count === 1 ? "" : "s"}
          </p>
        </div>

        <Link
          href={`/platform-admin/jobs/${job.id}`}
          className="shrink-0 text-sm font-medium text-brand hover:underline"
        >
          View details →
        </Link>
      </CardContent>
    </Card>
  );
}

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
