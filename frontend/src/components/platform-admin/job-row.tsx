import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatSalary } from "@/lib/format";
import { SHADOW_JOB_STATUS_LABEL, SHADOW_JOB_STATUS_VARIANT } from "@/lib/status-display";
import type { AdminShadowJob } from "@/lib/types";

export function JobRow({ job }: { job: AdminShadowJob }) {
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
