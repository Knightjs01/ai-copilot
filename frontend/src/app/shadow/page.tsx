"use client";

import * as React from "react";
import Link from "next/link";
import { Briefcase, MapPin, SearchX } from "lucide-react";

import { ShadowBoardToolbar } from "@/components/shadow/shadow-board-toolbar";
import { ShadowTopNav } from "@/components/shadow/shadow-top-nav";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useShadowBoard } from "@/lib/queries/shadow-jobs";
import { EMPLOYMENT_TYPE_LABEL, REMOTE_PREFERENCE_LABEL } from "@/lib/status-display";
import type { EmploymentType, RemotePreference } from "@/lib/types";
import styles from "./shadow-theme.module.css";

const MAX_REQUIREMENT_TAGS = 2;

function formatSalary(min: number | null, max: number | null): string | null {
  if (!min && !max) return null;
  const fmt = (n: number) => `£${(n / 1000).toFixed(0)}k`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  return fmt((min ?? max)!);
}

export default function ShadowBoardPage() {
  const [search, setSearch] = React.useState("");
  const [remotePreference, setRemotePreference] = React.useState<RemotePreference | "all">("all");
  const [employmentType, setEmploymentType] = React.useState<EmploymentType | "all">("all");
  const mainRef = React.useRef<HTMLElement>(null);

  const { data: jobs, isLoading } = useShadowBoard({
    remote_preference: remotePreference === "all" ? undefined : remotePreference,
    employment_type: employmentType === "all" ? undefined : employmentType,
  });

  const filteredJobs = React.useMemo(() => {
    if (!jobs) return [];
    const query = search.trim().toLowerCase();
    if (!query) return jobs;
    return jobs.filter(
      (job) =>
        job.title.toLowerCase().includes(query) ||
        job.summary.toLowerCase().includes(query) ||
        job.company_name.toLowerCase().includes(query)
    );
  }, [jobs, search]);

  return (
    // ShadowTopNav + this outer bg-slate-50 gutter stay light. Only <main> (the actual board
    // content) goes obsidian/blue — Shadow keeps its own distinct dark theme, separate from
    // Passport's, per the user's explicit call to not merge the two.
    <div className="min-h-screen bg-slate-50">
      <ShadowTopNav />
      <main ref={mainRef} className={`${styles.shadowTheme} mx-auto max-w-4xl rounded-2xl px-6 py-10`}>
        <div className="mb-8 flex flex-col gap-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            The job market you can enter without being seen
          </p>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            The Shadow job board
          </h1>
          <p className="max-w-xl text-sm text-muted-foreground">
            Apply with your Phantom Passport. Companies see your skills and experience, not your
            name, until you choose to reveal it.
          </p>
        </div>

        <div className="mb-6">
          <ShadowBoardToolbar
            search={search}
            onSearchChange={setSearch}
            remotePreference={remotePreference}
            onRemotePreferenceChange={setRemotePreference}
            employmentType={employmentType}
            onEmploymentTypeChange={setEmploymentType}
            matchCount={filteredJobs.length}
            totalCount={jobs?.length ?? 0}
            container={mainRef.current}
          />
        </div>

        {isLoading && (
          <div className="flex justify-center py-16">
            <Spinner className="h-6 w-6 text-muted-foreground" />
          </div>
        )}

        {!isLoading && jobs?.length === 0 && (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              No open roles right now. Check back soon.
            </CardContent>
          </Card>
        )}

        {!isLoading && (jobs?.length ?? 0) > 0 && filteredJobs.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
              <SearchX className="h-5 w-5 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No roles match your search right now.</p>
            </CardContent>
          </Card>
        )}

        <div className="flex flex-col gap-3">
          {filteredJobs.map((job) => {
            const salary = formatSalary(job.salary_min, job.salary_max);
            const extraRequirements = job.requirements.length - MAX_REQUIREMENT_TAGS;
            return (
              <Link key={job.id} href={`/shadow/jobs/${job.id}`}>
                <Card className="transition-colors hover:border-muted-foreground/40">
                  <CardContent className="flex flex-col gap-2.5 py-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex flex-col gap-0.5">
                        <h2 className="text-base font-semibold text-foreground">{job.title}</h2>
                        <p className="text-sm text-muted-foreground">{job.company_name}</p>
                      </div>
                      {salary && <Badge variant="success">{salary}</Badge>}
                    </div>
                    <p className="line-clamp-2 text-sm text-muted-foreground">{job.summary}</p>
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
                        <Badge variant="outline">
                          {REMOTE_PREFERENCE_LABEL[job.remote_preference]}
                        </Badge>
                      )}
                      {job.seniority && <Badge variant="neutral">{job.seniority}</Badge>}
                    </div>
                    {job.requirements.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5">
                        {job.requirements.slice(0, MAX_REQUIREMENT_TAGS).map((req) => (
                          <span
                            key={req}
                            className="rounded-full border border-border bg-secondary/40 px-2.5 py-0.5 text-[11px] text-foreground/80"
                          >
                            {req}
                          </span>
                        ))}
                        {extraRequirements > 0 && (
                          <span className="text-[11px] text-muted-foreground">
                            +{extraRequirements} more
                          </span>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </main>
    </div>
  );
}
