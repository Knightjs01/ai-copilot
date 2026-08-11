"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useMyApplications } from "@/lib/queries/shadow-jobs";
import { SHADOW_APPLICATION_STATUS_LABEL, SHADOW_APPLICATION_STATUS_VARIANT } from "@/lib/status-display";

export default function ApplicationsPage() {
  const { data: applications, isLoading } = useMyApplications();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Your applications</h1>
        <p className="text-sm text-muted-foreground">
          Each application gets its own Callsign — a company can never correlate you across
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
            You haven&apos;t applied to any roles yet — browse the{" "}
            <Link href="/shadow" className="font-medium text-foreground underline underline-offset-4">
              job board
            </Link>
            .
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col gap-3">
        {applications?.map((application) => (
          <Link key={application.id} href={`/shadow/applications/${application.id}`}>
            <Card className="transition-colors hover:border-slate-300">
              <CardContent className="flex items-center justify-between gap-4 py-5">
                <div className="flex flex-col gap-0.5">
                  <h2 className="text-base font-semibold text-foreground">
                    {application.job_title}
                  </h2>
                  <p className="text-sm text-muted-foreground">{application.company_name}</p>
                  <p className="text-xs text-muted-foreground">Callsign: {application.callsign}</p>
                </div>
                <Badge variant={SHADOW_APPLICATION_STATUS_VARIANT[application.status]}>
                  {SHADOW_APPLICATION_STATUS_LABEL[application.status]}
                </Badge>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
