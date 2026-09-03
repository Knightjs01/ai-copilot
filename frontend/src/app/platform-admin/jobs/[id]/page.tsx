"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { StatTile } from "@/components/ui/stat-tile";
import { Textarea } from "@/components/ui/textarea";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { JobIntelligenceCard } from "@/components/shadow/job-intelligence-card";
import { useAdminJob, useApproveJob, useRejectJob } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { formatSalary } from "@/lib/format";
import { SHADOW_JOB_STATUS_LABEL, SHADOW_JOB_STATUS_VARIANT } from "@/lib/status-display";

export default function PlatformAdminJobDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
  const { data: job, isLoading } = useAdminJob(params.id);
  const [rejecting, setRejecting] = React.useState(false);
  const [reason, setReason] = React.useState("");
  const approve = useApproveJob();
  const reject = useRejectJob();
  const isMutating = approve.isPending || reject.isPending;

  React.useEffect(() => {
    if (authLoading) return;
    if (!admin) router.push("/platform-admin/login");
    else if (!hasPermission("jobs.view")) router.push("/platform-admin");
  }, [authLoading, admin, hasPermission, router]);

  if (authLoading || !admin || !hasPermission("jobs.view") || isLoading || !job) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  const canReview = hasPermission("jobs.review") && job.status === "pending_review";

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />

      <Link
        href="/platform-admin/jobs"
        className="inline-flex w-fit items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Jobs
      </Link>

      <div className="flex flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold text-foreground">{job.title}</h1>
          <Badge variant={SHADOW_JOB_STATUS_VARIANT[job.status]}>
            {SHADOW_JOB_STATUS_LABEL[job.status]}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {job.company_name}
          {job.published_at &&
            ` · Published ${new Date(job.published_at).toLocaleDateString()}`}
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <StatTile label="Applicants" value={job.applicant_count} />
        <StatTile label="Matches computed" value={job.match_count} />
        <StatTile label="Interviews" value={job.interview_count} />
      </div>
      <p className="-mt-3 text-xs text-muted-foreground">
        Matches are computed as candidates and recruiters interact with this role — not every
        discoverable candidate has been scored yet.
      </p>

      <Card>
        <CardContent className="flex flex-col gap-3 py-5">
          <p className="text-sm text-muted-foreground">
            {job.department ? `${job.department} · ` : ""}
            {job.seniority ? `${job.seniority} · ` : ""}
            {job.employment_type} · {job.location ?? "Remote/unspecified"}
            {job.remote_preference ? ` · ${job.remote_preference}` : ""}
            {job.salary_min || job.salary_max
              ? ` · ${formatSalary(job.salary_min, job.salary_max)}`
              : ""}
          </p>
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
        </CardContent>
      </Card>

      {job.job_intelligence && <JobIntelligenceCard intelligence={job.job_intelligence} />}

      {canReview && (
        <Card>
          <CardContent className="flex flex-col gap-3 py-5">
            <p className="text-sm font-medium text-foreground">Moderation</p>
            {rejecting && (
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
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="brand"
                size="sm"
                onClick={() => approve.mutate(job.id)}
                disabled={isMutating}
              >
                {approve.isPending ? "Approving…" : "Approve"}
              </Button>
              {rejecting ? (
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => reject.mutate({ jobId: job.id, reason: reason || undefined })}
                  disabled={isMutating}
                >
                  {reject.isPending ? "Rejecting…" : "Confirm reject"}
                </Button>
              ) : (
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setRejecting(true)}
                  disabled={isMutating}
                >
                  Reject
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
