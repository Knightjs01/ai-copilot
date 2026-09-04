"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { useAdminCandidate } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { formatSalary } from "@/lib/format";
import { VERIFICATION_STATUS_LABEL, VERIFICATION_STATUS_VARIANT } from "@/lib/status-display";

export default function PlatformAdminCandidateDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { admin, isLoading: authLoading, hasPermission } = usePlatformAdminAuth();
  const { data: candidate, isLoading } = useAdminCandidate(params.id);

  React.useEffect(() => {
    if (authLoading) return;
    if (!admin) router.push("/platform-admin/login");
    else if (!hasPermission("candidates.view")) router.push("/platform-admin");
  }, [authLoading, admin, hasPermission, router]);

  if (authLoading || !admin || !hasPermission("candidates.view") || isLoading || !candidate) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />

      <Link
        href="/platform-admin/candidates"
        className="inline-flex w-fit items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Candidates
      </Link>

      <div className="flex flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold text-foreground">
            {candidate.callsign ?? "Not yet approved"}
          </h1>
          <Badge variant={VERIFICATION_STATUS_VARIANT[candidate.verification_status]}>
            {VERIFICATION_STATUS_LABEL[candidate.verification_status]}
          </Badge>
          <Badge variant="outline">{candidate.visibility}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Created {new Date(candidate.created_at).toLocaleDateString()}
        </p>
      </div>

      <Card>
        <CardContent className="flex flex-col gap-3 py-5">
          {candidate.headline && (
            <p className="text-base font-medium text-foreground">{candidate.headline}</p>
          )}
          <p className="text-sm text-muted-foreground">
            {[
              candidate.seniority,
              candidate.years_experience != null ? `${candidate.years_experience} yrs` : null,
              candidate.location,
              candidate.remote_preference,
              candidate.salary_min || candidate.salary_max
                ? formatSalary(candidate.salary_min, candidate.salary_max)
                : null,
              candidate.notice_period ? `Notice: ${candidate.notice_period}` : null,
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
          {candidate.summary && (
            <p className="whitespace-pre-wrap text-sm text-muted-foreground">
              {candidate.summary}
            </p>
          )}
          {candidate.skills.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {candidate.skills.map((skill) => (
                <Badge key={skill} variant="outline">
                  {skill}
                </Badge>
              ))}
            </div>
          )}
          {candidate.industries.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {candidate.industries.map((industry) => (
                <Badge key={industry} variant="outline">
                  {industry}
                </Badge>
              ))}
            </div>
          )}
          {candidate.career_entries.length > 0 && (
            <div className="flex flex-col gap-2 border-t border-border pt-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Career history
              </p>
              {candidate.career_entries.map((entry, i) => (
                <div key={i} className="text-sm">
                  <p className="font-medium text-foreground">
                    {entry.title} · {entry.company_name_anonymized}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {entry.start_date ?? "?"} – {entry.is_current ? "Present" : entry.end_date ?? "?"}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex flex-col gap-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Applications ({candidate.applications.length})
        </p>
        {candidate.applications.length === 0 && (
          <p className="py-4 text-center text-sm text-muted-foreground">No applications yet.</p>
        )}
        {candidate.applications.map((app) => (
          <Card key={app.shadow_job_id}>
            <CardContent className="flex flex-col gap-1 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-col gap-0.5">
                <p className="text-sm font-medium text-foreground">{app.job_title}</p>
                <p className="text-xs text-muted-foreground">
                  <Link
                    href={`/platform-admin/companies/${app.company_id}`}
                    className="hover:text-foreground hover:underline"
                  >
                    {app.company_name}
                  </Link>
                  {" · "}
                  {app.status} / {app.pipeline_stage}
                  {" · "}
                  {new Date(app.created_at).toLocaleDateString()}
                </p>
              </div>
              <Link
                href={`/platform-admin/jobs/${app.shadow_job_id}`}
                className="shrink-0 text-sm font-medium text-brand hover:underline"
              >
                View job →
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
