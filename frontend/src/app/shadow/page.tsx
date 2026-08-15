"use client";

import Link from "next/link";
import { Briefcase, MapPin } from "lucide-react";

import { ShadowTopNav } from "@/components/shadow/shadow-top-nav";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useShadowBoard } from "@/lib/queries/shadow-jobs";
import { EMPLOYMENT_TYPE_LABEL, REMOTE_PREFERENCE_LABEL } from "@/lib/status-display";
import styles from "./shadow-theme.module.css";

function formatSalary(min: number | null, max: number | null): string | null {
  if (!min && !max) return null;
  const fmt = (n: number) => `£${(n / 1000).toFixed(0)}k`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  return fmt((min ?? max)!);
}

export default function ShadowBoardPage() {
  const { data: jobs, isLoading } = useShadowBoard();

  return (
    // ShadowTopNav + this outer bg-slate-50 gutter stay light. Only <main> (the actual board
    // content) goes obsidian/blue — Shadow keeps its own distinct dark theme, separate from
    // Passport's, per the user's explicit call to not merge the two.
    <div className="min-h-screen bg-slate-50">
      <ShadowTopNav />
      <main className={`${styles.shadowTheme} mx-auto max-w-4xl rounded-2xl px-6 py-10`}>
        <div className="mb-8 flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            The Shadow job board
          </h1>
          <p className="text-sm text-muted-foreground">
            Apply with your Phantom Passport. Companies see your skills and experience, not your
            name, until you choose to reveal it.
          </p>
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

        <div className="flex flex-col gap-3">
          {jobs?.map((job) => {
            const salary = formatSalary(job.salary_min, job.salary_max);
            return (
              <Link key={job.id} href={`/shadow/jobs/${job.id}`}>
                <Card className="transition-colors hover:border-muted-foreground/40">
                  <CardContent className="flex flex-col gap-2 py-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex flex-col gap-0.5">
                        <h2 className="text-base font-semibold text-foreground">{job.title}</h2>
                        <p className="text-sm text-muted-foreground">{job.company_name}</p>
                      </div>
                      {salary && <Badge variant="success">{salary}</Badge>}
                    </div>
                    <p className="line-clamp-2 text-sm text-muted-foreground">{job.summary}</p>
                    <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
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
