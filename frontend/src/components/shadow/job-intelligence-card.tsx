import type { ReactNode } from "react";
import { Banknote, Clock, type LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import type { JobIntelligence } from "@/lib/types";

const VS_MEDIAN_LABEL: Record<"above" | "at" | "below", string> = {
  above: "above the median for similar roles",
  at: "right at the median for similar roles",
  below: "below the median for similar roles",
};

function IntelligenceRow({
  icon: Icon,
  title,
  children,
}: {
  icon: LucideIcon;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand/10 text-brand">
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex flex-col gap-0.5">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {title}
        </p>
        <div className="text-sm text-foreground">{children}</div>
      </div>
    </div>
  );
}

// Real aggregations (see backend shadow_jobs/service.py::compute_salary_benchmark/
// compute_view_time_benchmark), gated on a minimum sample size. The "not enough data yet" state
// is the honest, expected common case for a young marketplace -- deliberately plain muted text,
// not the site's (Preview) badge convention, since the pipeline itself is real and live, just
// data-sparse for this particular job/company right now.
export function JobIntelligenceCard({ intelligence }: { intelligence: JobIntelligence }) {
  const { salary_benchmark: salary, view_time_benchmark: viewTime } = intelligence;

  return (
    <Card>
      <CardContent className="flex flex-col gap-4 py-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Job Intelligence
        </p>

        <IntelligenceRow icon={Banknote} title="Salary">
          {salary.has_enough_data && salary.median !== null ? (
            <p>
              This role&apos;s salary is{" "}
              <span className="font-medium">
                {salary.this_job_vs_median && VS_MEDIAN_LABEL[salary.this_job_vs_median]}
              </span>{" "}
              — £{Math.round(salary.median / 1000)}k, based on {salary.sample_size} comparable
              roles across {salary.company_count} companies.
            </p>
          ) : (
            <p className="text-muted-foreground">
              Not enough comparable roles published yet to benchmark this salary.
            </p>
          )}
        </IntelligenceRow>

        <IntelligenceRow icon={Clock} title="Typical response">
          {viewTime.has_enough_data && viewTime.median_hours !== null ? (
            <p>
              Companies like this typically view new applications within{" "}
              <span className="font-medium">
                {viewTime.median_hours < 24
                  ? `${Math.round(viewTime.median_hours)} hours`
                  : `${Math.round(viewTime.median_hours / 24)} days`}
              </span>
              .
            </p>
          ) : (
            <p className="text-muted-foreground">
              Not enough data yet on how quickly this company reviews applications.
            </p>
          )}
        </IntelligenceRow>
      </CardContent>
    </Card>
  );
}
