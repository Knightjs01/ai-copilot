"use client";

import * as React from "react";
import Link from "next/link";

import { useShadowCopilot } from "@/components/shadow/shadow-copilot-provider";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useMyApplications } from "@/lib/queries/shadow-jobs";
import {
  SHADOW_APPLICATION_STATUS_COLUMNS,
  SHADOW_APPLICATION_STATUS_LABEL,
} from "@/lib/status-display";
import type { ShadowApplication, ShadowApplicationStatus } from "@/lib/types";

function formatAppliedDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function ApplicationKanbanCard({ application }: { application: ShadowApplication }) {
  return (
    <Link href={`/shadow/applications/${application.id}`}>
      <div className="rounded-2xl border border-border bg-card p-3.5 shadow-sm shadow-slate-900/[0.03] transition-shadow hover:border-slate-300">
        <p className="text-sm font-semibold text-foreground">{application.job_title}</p>
        <p className="text-xs text-muted-foreground">{application.company_name}</p>
        <div className="mt-2 flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
          <span>Callsign: {application.callsign}</span>
          <span>{formatAppliedDate(application.applied_at)}</span>
        </div>
      </div>
    </Link>
  );
}

function ApplicationKanbanColumn({
  status,
  applications,
}: {
  status: ShadowApplicationStatus;
  applications: ShadowApplication[];
}) {
  return (
    <div className="flex w-72 shrink-0 flex-col gap-3 rounded-2xl border border-transparent p-2">
      <div className="flex items-center gap-2 px-2 pt-1">
        <h3 className="text-sm font-semibold text-foreground">
          {SHADOW_APPLICATION_STATUS_LABEL[status]}
        </h3>
        <span className="rounded-full bg-secondary px-2 py-0.5 text-xs font-medium text-muted-foreground">
          {applications.length}
        </span>
      </div>
      <div className="flex flex-col gap-2">
        {applications.map((application) => (
          <ApplicationKanbanCard key={application.id} application={application} />
        ))}
      </div>
    </div>
  );
}

export default function ApplicationsPage() {
  const { data: applications, isLoading } = useMyApplications();
  const { setContext } = useShadowCopilot();

  React.useEffect(() => {
    setContext({ type: "application" });
    return () => setContext({ type: "none" });
  }, [setContext]);

  const byStatus = React.useMemo(() => {
    const map = new Map<ShadowApplicationStatus, ShadowApplication[]>();
    for (const status of SHADOW_APPLICATION_STATUS_COLUMNS) map.set(status, []);
    for (const application of applications ?? []) {
      map.get(application.status)?.push(application);
    }
    return map;
  }, [applications]);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Your applications</h1>
        <p className="text-sm text-muted-foreground">
          Each application gets its own Callsign. A company can never correlate you across
          projects.
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && applications?.length === 0 && (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            You haven&apos;t applied to any roles yet. Browse{" "}
            <Link href="/shadow" className="font-medium text-foreground underline underline-offset-4">
              Discover
            </Link>
            .
          </CardContent>
        </Card>
      )}

      {!isLoading && (applications?.length ?? 0) > 0 && (
        <div className="flex gap-4 overflow-x-auto pb-2">
          {SHADOW_APPLICATION_STATUS_COLUMNS.map((status) => (
            <ApplicationKanbanColumn
              key={status}
              status={status}
              applications={byStatus.get(status) ?? []}
            />
          ))}
        </div>
      )}
    </div>
  );
}
