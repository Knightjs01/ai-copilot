"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { Briefcase, MapPin } from "lucide-react";

import { ShadowTopNav } from "@/components/shadow/shadow-top-nav";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { ApiError } from "@/lib/api-client";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useApplyToShadowJob, useShadowBoardJob } from "@/lib/queries/shadow-jobs";
import { EMPLOYMENT_TYPE_LABEL, REMOTE_PREFERENCE_LABEL } from "@/lib/status-display";

function formatSalary(min: number | null, max: number | null): string | null {
  if (!min && !max) return null;
  const fmt = (n: number) => `£${(n / 1000).toFixed(0)}k`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  return fmt((min ?? max)!);
}

export default function ShadowJobDetailPage() {
  const params = useParams<{ jobId: string }>();
  const router = useRouter();
  const { candidate, isLoading: authLoading } = useCandidateAuth();
  const { data: job, isLoading } = useShadowBoardJob(params.jobId);
  const applyMutation = useApplyToShadowJob(params.jobId);
  const [applyError, setApplyError] = React.useState<string | null>(null);
  const [applied, setApplied] = React.useState(false);

  const handleApply = async () => {
    setApplyError(null);
    if (!candidate) {
      router.push("/shadow/signup");
      return;
    }
    try {
      await applyMutation.mutateAsync();
      setApplied(true);
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setApplyError("Build your Phantom Passport before applying.");
      } else if (err instanceof ApiError && err.status === 409) {
        setApplyError("You've already applied to this role.");
      } else {
        setApplyError("Couldn't submit your application — try again.");
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <ShadowTopNav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        {(isLoading || authLoading) && (
          <div className="flex justify-center py-16">
            <Spinner className="h-6 w-6 text-muted-foreground" />
          </div>
        )}

        {!isLoading && !job && (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              This role isn&apos;t open for applications anymore.
            </CardContent>
          </Card>
        )}

        {job && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">{job.title}</h1>
              <p className="text-sm text-muted-foreground">{job.company_name}</p>
              <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                {job.location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {job.location}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <Briefcase className="h-3.5 w-3.5" />
                  {EMPLOYMENT_TYPE_LABEL[job.employment_type]}
                </span>
                {job.remote_preference && (
                  <Badge variant="outline">{REMOTE_PREFERENCE_LABEL[job.remote_preference]}</Badge>
                )}
                {job.seniority && <Badge variant="neutral">{job.seniority}</Badge>}
                {formatSalary(job.salary_min, job.salary_max) && (
                  <Badge variant="success">{formatSalary(job.salary_min, job.salary_max)}</Badge>
                )}
              </div>
            </div>

            <Card>
              <CardContent className="flex flex-col gap-4 py-6">
                <p className="whitespace-pre-line text-sm text-foreground">{job.description}</p>
                {job.requirements.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <h3 className="text-sm font-semibold text-foreground">Requirements</h3>
                    <ul className="list-inside list-disc text-sm text-muted-foreground">
                      {job.requirements.map((req, i) => (
                        <li key={i}>{req}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="flex flex-col items-start gap-3 py-6">
                {applied ? (
                  <p className="text-sm font-medium text-success">
                    Application submitted — track its status from your Applications page.
                  </p>
                ) : (
                  <>
                    <p className="text-sm text-muted-foreground">
                      One-click apply with whatever your Phantom Passport already holds — nothing
                      new to fill in.
                    </p>
                    {applyError && <p className="text-sm font-medium text-danger">{applyError}</p>}
                    <Button
                      variant="brand"
                      size="lg"
                      onClick={handleApply}
                      disabled={applyMutation.isPending}
                    >
                      {applyMutation.isPending
                        ? "Applying…"
                        : candidate
                          ? "Apply with Phantom Passport"
                          : "Sign up to apply"}
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
