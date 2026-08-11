"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { ShieldAlert } from "lucide-react";

import { ApplicantCard } from "@/components/shadow-jobs/applicant-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/lib/auth-context";
import {
  useCloseShadowJob,
  useMyShadowJob,
  usePublishShadowJob,
  useShadowJobApplicants,
  useUpdateShadowJob,
} from "@/lib/queries/shadow-jobs";
import { SHADOW_JOB_STATUS_LABEL, SHADOW_JOB_STATUS_VARIANT } from "@/lib/status-display";

export default function ShadowJobDetailPage() {
  const params = useParams<{ jobId: string }>();
  const { hasPermission } = useAuth();
  const canView = hasPermission("shadow_jobs.view");
  const canUpdate = hasPermission("shadow_jobs.update");
  const { data: job, isLoading } = useMyShadowJob(params.jobId);
  const { data: applicants, isLoading: applicantsLoading } = useShadowJobApplicants(params.jobId);
  const updateJob = useUpdateShadowJob(params.jobId);
  const publishJob = usePublishShadowJob(params.jobId);
  const closeJob = useCloseShadowJob(params.jobId);

  const [summary, setSummary] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [isDirty, setIsDirty] = React.useState(false);

  React.useEffect(() => {
    if (isDirty || !job) return;
    setSummary(job.summary);
    setDescription(job.description);
    setLocation(job.location ?? "");
  }, [job, isDirty]);

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Shadow Jobs isn&apos;t available on your role</p>
      </div>
    );
  }

  if (isLoading || !job) {
    return (
      <div className="flex justify-center py-24">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  const handleSave = () => {
    updateJob.mutate(
      { summary, description, location: location || null },
      { onSuccess: () => setIsDirty(false) }
    );
  };

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{job.title}</h1>
          <p className="text-sm text-muted-foreground">
            {job.department || "No department set"} · {job.applicant_count} applicant
            {job.applicant_count === 1 ? "" : "s"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={SHADOW_JOB_STATUS_VARIANT[job.status]}>
            {SHADOW_JOB_STATUS_LABEL[job.status]}
          </Badge>
          {canUpdate && job.status === "draft" && (
            <Button size="sm" onClick={() => publishJob.mutate()} disabled={publishJob.isPending}>
              {publishJob.isPending ? "Publishing…" : "Publish"}
            </Button>
          )}
          {canUpdate && job.status === "published" && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => closeJob.mutate()}
              disabled={closeJob.isPending}
            >
              {closeJob.isPending ? "Closing…" : "Close"}
            </Button>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Listing</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Field label="Location" htmlFor="location">
            <Input
              id="location"
              value={location}
              disabled={!canUpdate}
              onChange={(e) => {
                setLocation(e.target.value);
                setIsDirty(true);
              }}
            />
          </Field>
          <Field label="Summary" htmlFor="summary">
            <Textarea
              id="summary"
              value={summary}
              disabled={!canUpdate}
              onChange={(e) => {
                setSummary(e.target.value);
                setIsDirty(true);
              }}
            />
          </Field>
          <Field label="Full description" htmlFor="description">
            <Textarea
              id="description"
              value={description}
              disabled={!canUpdate}
              onChange={(e) => {
                setDescription(e.target.value);
                setIsDirty(true);
              }}
            />
          </Field>
          {canUpdate && (
            <div className="flex justify-end">
              <Button size="sm" onClick={handleSave} disabled={!isDirty || updateJob.isPending}>
                {updateJob.isPending ? "Saving…" : "Save"}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold tracking-tight text-foreground">Applicants</h2>
        {applicantsLoading ? (
          <div className="flex justify-center py-12">
            <Spinner className="h-6 w-6 text-muted-foreground" />
          </div>
        ) : applicants && applicants.length > 0 ? (
          <div className="flex flex-col gap-3">
            {applicants.map((profile) => (
              <ApplicantCard key={profile.application_id} jobId={job.id} profile={profile} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-border py-16 text-center">
            <p className="text-sm font-medium text-foreground">No applicants yet</p>
            <p className="max-w-xs text-sm text-muted-foreground">
              Once this job is published, applicants will show up here anonymously.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
