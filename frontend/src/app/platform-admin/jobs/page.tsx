"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Briefcase } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { useApproveJob, usePendingReviewJobs, useRejectJob } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { formatSalary } from "@/lib/format";
import type { AdminShadowJob } from "@/lib/types";

function JobReviewCard({ job, canReview }: { job: AdminShadowJob; canReview: boolean }) {
  const [expanded, setExpanded] = React.useState(false);
  const [rejecting, setRejecting] = React.useState(false);
  const [reason, setReason] = React.useState("");
  const approve = useApproveJob();
  const reject = useRejectJob();
  const isPending = approve.isPending || reject.isPending;

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-5">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-foreground">{job.title}</h3>
            <Badge variant="outline">{job.company_name}</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {job.department ? `${job.department} · ` : ""}
            {job.location ?? "Remote/unspecified"}
            {job.salary_min || job.salary_max
              ? ` · ${formatSalary(job.salary_min, job.salary_max)}`
              : ""}
          </p>
        </div>

        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="self-start text-sm font-medium text-brand hover:underline"
        >
          {expanded ? "Hide full listing" : "View full listing"}
        </button>

        {expanded && (
          <div className="flex flex-col gap-3 rounded-xl border border-border bg-secondary/40 p-4 text-sm">
            <p className="whitespace-pre-wrap text-foreground">{job.summary}</p>
            <p className="whitespace-pre-wrap text-muted-foreground">{job.description}</p>
            {job.requirements.length > 0 && (
              <ul className="list-inside list-disc text-muted-foreground">
                {job.requirements.map((req, i) => (
                  <li key={i}>{String(req)}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {canReview && rejecting && (
          <Textarea
            placeholder="Reason (optional)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={2}
          />
        )}

        {(approve.isError || reject.isError) && (
          <p className="text-sm font-medium text-danger">Couldn&apos;t save. Try again.</p>
        )}

        {canReview && (
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="brand"
              size="sm"
              onClick={() => approve.mutate(job.id)}
              disabled={isPending}
            >
              {approve.isPending ? "Approving…" : "Approve"}
            </Button>
            {rejecting ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() =>
                  reject.mutate({ jobId: job.id, reason: reason || undefined })
                }
                disabled={isPending}
              >
                {reject.isPending ? "Rejecting…" : "Confirm reject"}
              </Button>
            ) : (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setRejecting(true)}
                disabled={isPending}
              >
                Reject
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function PlatformAdminJobsPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
  const { data: jobs, isLoading } = usePendingReviewJobs();

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

  const canReview = hasPermission("jobs.review");

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && jobs?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <Briefcase className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No jobs waiting for review.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && jobs && jobs.length > 0 && (
        <div className="flex flex-col gap-3">
          {jobs.map((job) => (
            <JobReviewCard key={job.id} job={job} canReview={canReview} />
          ))}
        </div>
      )}
    </div>
  );
}
