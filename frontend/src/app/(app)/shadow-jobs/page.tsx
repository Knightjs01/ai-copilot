"use client";

import Link from "next/link";
import { ShieldAlert } from "lucide-react";

import { NewShadowJobDialog } from "@/components/shadow-jobs/new-shadow-job-dialog";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";
import { useMyShadowJobs } from "@/lib/queries/shadow-jobs";
import { SHADOW_JOB_STATUS_LABEL, SHADOW_JOB_STATUS_VARIANT } from "@/lib/status-display";

export default function ShadowJobsPage() {
  const { hasPermission } = useAuth();
  const canView = hasPermission("shadow_jobs.view");
  const canCreate = hasPermission("shadow_jobs.create");
  const { data: jobs, isLoading } = useMyShadowJobs();

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Shadow Jobs isn&apos;t available on your role</p>
        <p className="max-w-xs text-sm text-muted-foreground">
          Ask an Owner or Admin on your team for access.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Shadow Jobs</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Post to the anonymous job board — applicants stay pseudonymous until you request and
            they approve a reveal.
          </p>
        </div>
        {canCreate && <NewShadowJobDialog />}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-24">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      ) : jobs && jobs.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <Link key={job.id} href={`/shadow-jobs/${job.id}`}>
              <Card className="h-full transition-shadow hover:shadow-md hover:shadow-slate-900/[0.06]">
                <CardHeader className="flex-row items-start justify-between gap-2 space-y-0">
                  <CardTitle>{job.title}</CardTitle>
                  <Badge variant={SHADOW_JOB_STATUS_VARIANT[job.status]}>
                    {SHADOW_JOB_STATUS_LABEL[job.status]}
                  </Badge>
                </CardHeader>
                <CardContent className="flex flex-col gap-1">
                  <p className="text-sm text-muted-foreground">
                    {job.department || "No department set"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {job.applicant_count} applicant{job.applicant_count === 1 ? "" : "s"}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
          <p className="text-sm font-medium text-foreground">No Shadow jobs yet</p>
          <p className="max-w-xs text-sm text-muted-foreground">
            Post a role to start receiving anonymous applications.
          </p>
        </div>
      )}
    </div>
  );
}
