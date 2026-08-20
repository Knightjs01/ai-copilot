"use client";

import Link from "next/link";
import { Bell, BellOff, Bookmark, BookmarkX, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useDeleteJobAlert, useJobAlerts, useUpdateJobAlert } from "@/lib/queries/job-alerts";
import { useSavedJobs, useUnsaveJob } from "@/lib/queries/saved-jobs";
import { EMPLOYMENT_TYPE_LABEL, REMOTE_PREFERENCE_LABEL } from "@/lib/status-display";
import type { JobAlert, SavedShadowJob } from "@/lib/types";

function describeAlert(alert: JobAlert): string {
  if (alert.name) return alert.name;
  const parts = [
    alert.seniority,
    alert.remote_preference ? REMOTE_PREFERENCE_LABEL[alert.remote_preference] : null,
    alert.employment_type ? EMPLOYMENT_TYPE_LABEL[alert.employment_type] : null,
    alert.location,
  ].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : "Job alert";
}

function JobAlertRow({ alert }: { alert: JobAlert }) {
  const updateAlert = useUpdateJobAlert(alert.id);
  const deleteAlert = useDeleteJobAlert();

  return (
    <Card>
      <CardContent className="flex items-center justify-between gap-4 py-4">
        <div className="flex flex-col gap-0.5">
          <p className="text-sm font-medium text-foreground">{describeAlert(alert)}</p>
          <p className="text-xs text-muted-foreground">
            {alert.is_active ? "Emailing you about new matches" : "Paused"}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => updateAlert.mutate({ is_active: !alert.is_active })}
            disabled={updateAlert.isPending}
          >
            {alert.is_active ? (
              <>
                <BellOff className="h-3.5 w-3.5" /> Pause
              </>
            ) : (
              <>
                <Bell className="h-3.5 w-3.5" /> Resume
              </>
            )}
          </Button>
          <button
            type="button"
            onClick={() => deleteAlert.mutate(alert.id)}
            disabled={deleteAlert.isPending}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-danger"
            aria-label="Delete job alert"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </CardContent>
    </Card>
  );
}

function formatSalary(min: number | null, max: number | null): string | null {
  if (!min && !max) return null;
  const fmt = (n: number) => `£${(n / 1000).toFixed(0)}k`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  return fmt((min ?? max)!);
}

function groupByCollection(saved: SavedShadowJob[]): Map<string, SavedShadowJob[]> {
  const groups = new Map<string, SavedShadowJob[]>();
  for (const item of saved) {
    const key = item.collection_name ?? "Saved";
    const existing = groups.get(key);
    if (existing) existing.push(item);
    else groups.set(key, [item]);
  }
  return groups;
}

export default function SavedJobsPage() {
  const { data: savedJobs, isLoading } = useSavedJobs();
  const unsaveJob = useUnsaveJob();
  const { data: jobAlerts, isLoading: alertsLoading } = useJobAlerts();

  const groups = savedJobs ? groupByCollection(savedJobs) : new Map<string, SavedShadowJob[]>();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Saved jobs</h1>
        <p className="text-sm text-muted-foreground">Roles you want to revisit.</p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && savedJobs?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
            <Bookmark className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Save roles you want to revisit.{" "}
              <Link href="/shadow" className="font-medium text-foreground underline underline-offset-4">
                Browse Discover
              </Link>
              .
            </p>
          </CardContent>
        </Card>
      )}

      {[...groups.entries()].map(([collectionName, jobs]) => (
        <div key={collectionName} className="flex flex-col gap-3">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {collectionName}
          </h2>
          <div className="flex flex-col gap-3">
            {jobs.map((saved) => {
              const salary = formatSalary(saved.job.salary_min, saved.job.salary_max);
              return (
                <Card key={saved.id} className="transition-colors hover:border-muted-foreground/40">
                  <CardContent className="flex items-start justify-between gap-4 py-5">
                    <Link href={`/shadow/jobs/${saved.job.id}`} className="flex flex-1 flex-col gap-1">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex flex-col gap-0.5">
                          <h3 className="text-base font-semibold text-foreground">
                            {saved.job.title}
                          </h3>
                          <p className="text-sm text-muted-foreground">{saved.job.company_name}</p>
                        </div>
                        {salary && <Badge variant="success">{salary}</Badge>}
                      </div>
                      <p className="line-clamp-2 text-sm text-muted-foreground">
                        {saved.job.summary}
                      </p>
                    </Link>
                    <button
                      type="button"
                      onClick={() => unsaveJob.mutate(saved.job.id)}
                      disabled={unsaveJob.isPending}
                      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-danger"
                      aria-label="Remove from saved jobs"
                    >
                      <BookmarkX className="h-4 w-4" />
                    </button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      ))}

      <div className="flex flex-col gap-3 border-t border-border pt-6">
        <div className="flex flex-col gap-1">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Job alerts
          </h2>
          <p className="text-sm text-muted-foreground">
            Save a search from the job board to get emailed when a new role matches.
          </p>
        </div>

        {alertsLoading && (
          <div className="flex justify-center py-8">
            <Spinner className="h-5 w-5 text-muted-foreground" />
          </div>
        )}

        {!alertsLoading && jobAlerts?.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center gap-2 py-8 text-center">
              <p className="text-sm text-muted-foreground">
                No job alerts yet.{" "}
                <Link href="/shadow" className="font-medium text-foreground underline underline-offset-4">
                  Save a search
                </Link>{" "}
                from the board.
              </p>
            </CardContent>
          </Card>
        )}

        {!alertsLoading && jobAlerts && jobAlerts.length > 0 && (
          <div className="flex flex-col gap-3">
            {jobAlerts.map((alert) => (
              <JobAlertRow key={alert.id} alert={alert} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
