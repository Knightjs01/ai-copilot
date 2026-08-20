"use client";

import * as React from "react";
import Link from "next/link";
import { Check } from "lucide-react";

import { useShadowCopilot } from "@/components/shadow/shadow-copilot-provider";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useMyApplications } from "@/lib/queries/shadow-jobs";
import { SHADOW_APPLICATION_STATUS_LABEL, SHADOW_APPLICATION_STATUS_VARIANT } from "@/lib/status-display";
import { cn } from "@/lib/utils";
import type { ShadowApplication, ShadowApplicationStatus } from "@/lib/types";

// The real, in-progress path a submitted application can move through -- reveal_requested only
// happens if a company actually asks, so it's still shown as a step even though not every
// application reaches it. declined/withdrawn are exits, not further steps along this path, so
// they're deliberately not part of the stepper (see the flat badge treatment below instead).
const ACTIVE_STEPS: ShadowApplicationStatus[] = [
  "submitted",
  "under_review",
  "reveal_requested",
  "revealed",
];
const TERMINAL_STATUSES = new Set<ShadowApplicationStatus>(["declined", "withdrawn"]);

function ApplicationStepper({ status }: { status: ShadowApplicationStatus }) {
  const currentIndex = ACTIVE_STEPS.indexOf(status);
  return (
    <div className="flex items-center gap-2">
      {ACTIVE_STEPS.map((step, index) => {
        const isComplete = index < currentIndex;
        const isCurrent = index === currentIndex;
        return (
          <div key={step} className="flex flex-1 items-center gap-2">
            <div className="flex flex-col items-center gap-1">
              <span
                className={cn(
                  "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] font-semibold",
                  isComplete
                    ? "border-brand bg-brand text-brand-foreground"
                    : isCurrent
                      ? "border-brand text-brand"
                      : "border-border text-muted-foreground"
                )}
              >
                {isComplete ? <Check className="h-3 w-3" /> : index + 1}
              </span>
              <span
                className={cn(
                  "hidden text-center text-[10px] sm:block",
                  isCurrent ? "font-medium text-foreground" : "text-muted-foreground"
                )}
              >
                {SHADOW_APPLICATION_STATUS_LABEL[step]}
              </span>
            </div>
            {index < ACTIVE_STEPS.length - 1 && (
              <span
                className={cn("h-px flex-1", index < currentIndex ? "bg-brand" : "bg-border")}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function ApplicationCard({ application }: { application: ShadowApplication }) {
  const isTerminal = TERMINAL_STATUSES.has(application.status);
  return (
    <Link href={`/shadow/applications/${application.id}`}>
      <Card className="transition-colors hover:border-brand/40">
        <CardContent className="flex flex-col gap-3 py-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex flex-col gap-0.5">
              <h3 className="text-base font-semibold text-foreground">{application.job_title}</h3>
              <p className="text-sm text-muted-foreground">{application.company_name}</p>
              <p className="text-xs text-muted-foreground">Callsign: {application.callsign}</p>
            </div>
            {isTerminal && (
              <Badge variant={SHADOW_APPLICATION_STATUS_VARIANT[application.status]}>
                {SHADOW_APPLICATION_STATUS_LABEL[application.status]}
              </Badge>
            )}
          </div>
          {!isTerminal && <ApplicationStepper status={application.status} />}
        </CardContent>
      </Card>
    </Link>
  );
}

export default function ApplicationsPage() {
  const { data: applications, isLoading } = useMyApplications();
  const { setContext } = useShadowCopilot();

  React.useEffect(() => {
    setContext({ type: "application" });
    return () => setContext({ type: "none" });
  }, [setContext]);

  const active = applications?.filter((a) => !TERMINAL_STATUSES.has(a.status)) ?? [];
  const completed = applications?.filter((a) => TERMINAL_STATUSES.has(a.status)) ?? [];

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

      {active.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Active
          </h2>
          <div className="flex flex-col gap-3">
            {active.map((application) => (
              <ApplicationCard key={application.id} application={application} />
            ))}
          </div>
        </div>
      )}

      {completed.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Completed
          </h2>
          <div className="flex flex-col gap-3">
            {completed.map((application) => (
              <ApplicationCard key={application.id} application={application} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
