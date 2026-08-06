"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useProjectAnalytics } from "@/lib/queries/analytics";
import {
  CANDIDATE_SOURCE_LABEL,
  CANDIDATE_STATUS_COLUMNS,
  CANDIDATE_STATUS_LABEL,
  NOTICE_PERIOD_LABEL,
} from "@/lib/status-display";
import type { CandidateSource, CandidateStatus, NoticePeriod } from "@/lib/types";

const BRAND_PURPLE = "#6651B0";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
  }).format(value);
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="flex flex-col gap-1 rounded-xl border border-border bg-white px-4 py-3">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <span className="text-xl font-semibold tracking-tight text-foreground">{value}</span>
      {sub && <span className="text-xs text-muted-foreground">{sub}</span>}
    </div>
  );
}

function BreakdownChart({ data }: { data: { label: string; count: number }[] }) {
  if (data.length === 0) {
    return <p className="text-sm text-muted-foreground">No data yet.</p>;
  }
  return (
    <ResponsiveContainer width="100%" height={Math.max(120, data.length * 40)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(214 32% 91%)" />
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="label" width={110} tick={{ fontSize: 12 }} />
        <Tooltip cursor={{ fill: "hsl(210 40% 96%)" }} />
        <Bar dataKey="count" fill={BRAND_PURPLE} radius={[0, 6, 6, 0]} barSize={18} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ProjectAnalyticsCard({ projectId }: { projectId: string }) {
  const { data, isLoading } = useProjectAnalytics(projectId);

  if (isLoading || !data) {
    return (
      <Card>
        <CardContent className="flex justify-center py-10">
          <Spinner className="h-5 w-5 text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (data.total_candidates === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Candidate pool snapshot</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Add candidates to this project to see a snapshot of the pool.
          </p>
        </CardContent>
      </Card>
    );
  }

  const statusData = CANDIDATE_STATUS_COLUMNS.filter(
    (status) => data.status_breakdown[status]
  ).map((status) => ({
    label: CANDIDATE_STATUS_LABEL[status as CandidateStatus],
    count: data.status_breakdown[status] ?? 0,
  }));

  const fitRatingData = Object.entries(data.fit_rating_breakdown).map(([label, count]) => ({
    label,
    count,
  }));

  const sourceData = Object.entries(data.source_breakdown).map(([source, count]) => ({
    label: CANDIDATE_SOURCE_LABEL[source as CandidateSource] ?? source,
    count,
  }));

  const agencyData = Object.entries(data.agency_breakdown)
    .sort((a, b) => b[1] - a[1])
    .map(([label, count]) => ({ label, count }));

  const locationData = Object.entries(data.location_breakdown)
    .sort((a, b) => b[1] - a[1])
    .map(([label, count]) => ({ label, count }));

  const noticePeriodData = Object.entries(data.notice_period_breakdown).map(
    ([noticePeriod, count]) => ({
      label: NOTICE_PERIOD_LABEL[noticePeriod as NoticePeriod] ?? noticePeriod,
      count,
    })
  );

  const currentEmployerData = Object.entries(data.current_employer_breakdown)
    .sort((a, b) => b[1] - a[1])
    .map(([label, count]) => ({ label, count }));

  const { salary_stats: salary } = data;
  const agencyCount = data.source_breakdown.agency ?? 0;
  const directCount = data.source_breakdown.direct ?? 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Candidate pool snapshot</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="Total candidates" value={String(data.total_candidates)} />
          <StatCard
            label="Average expected salary"
            value={salary.average != null ? formatCurrency(salary.average) : "—"}
            sub={
              salary.count > 0
                ? `from ${salary.count} candidate${salary.count === 1 ? "" : "s"}`
                : "no salary data yet"
            }
          />
          <StatCard
            label="Salary range"
            value={
              salary.minimum != null && salary.maximum != null
                ? `${formatCurrency(salary.minimum)} – ${formatCurrency(salary.maximum)}`
                : "—"
            }
          />
          <StatCard
            label="Direct vs agency"
            value={`${directCount} / ${agencyCount}`}
            sub={agencyCount > 0 ? `across ${agencyData.length} agenc${agencyData.length === 1 ? "y" : "ies"}` : undefined}
          />
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-medium text-foreground">Pipeline stage</h3>
            <BreakdownChart data={statusData} />
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-medium text-foreground">AI fit rating</h3>
            <BreakdownChart data={fitRatingData} />
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-medium text-foreground">Source</h3>
            <BreakdownChart data={sourceData} />
          </div>
          {agencyData.length > 0 && (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium text-foreground">Submissions by agency</h3>
              <BreakdownChart data={agencyData} />
            </div>
          )}
          {noticePeriodData.length > 0 && (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium text-foreground">Notice period</h3>
              <BreakdownChart data={noticePeriodData} />
            </div>
          )}
          {locationData.length > 0 && (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium text-foreground">Location</h3>
              <BreakdownChart data={locationData} />
            </div>
          )}
          {currentEmployerData.length > 0 && (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium text-foreground">Current employer</h3>
              <BreakdownChart data={currentEmployerData} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
