import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { CornerMarks } from "@/components/marketing/mockups/corner-marks";
import { Badge } from "@/components/ui/badge";

// Mirrors the real ProjectAnalytics shape (status/fit_rating/source breakdowns, all computed
// within a single project) — illustrative sample numbers, same convention as every other
// mockup on this site, not fictional market data.
const FIT_RATING_ROWS = [
  { label: "Strong Fit", value: 34 },
  { label: "Good Fit", value: 28 },
  { label: "Possible Fit", value: 22 },
  { label: "Weak Fit", value: 16 },
];

const STATUS_ROWS = [
  { label: "Screening", value: 41 },
  { label: "Interviewing", value: 24 },
  { label: "Offer", value: 9 },
];

const SOURCE_ROWS = [
  { label: "Shadow board", value: 46 },
  { label: "Direct sourcing", value: 31 },
  { label: "Agency", value: 23 },
];

function BreakdownPanel({
  label,
  rows,
  barClass,
}: {
  label: string;
  rows: { label: string; value: number }[];
  barClass: (label: string) => string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-3.5">
      <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
      <div className="mt-2.5 flex flex-col gap-2">
        {rows.map((row) => (
          <div key={row.label} className="flex items-center gap-2.5">
            <span className="w-24 shrink-0 text-xs text-foreground/80">{row.label}</span>
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-secondary/60">
              <div className={barClass(row.label)} style={{ width: `${row.value}%` }} />
            </div>
            <span className="w-9 shrink-0 text-right font-mono text-xs tabular-nums text-muted-foreground">
              {row.value}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function IntelligenceBreakdownMockup() {
  return (
    <div className="relative">
      <CornerMarks />
      <BrowserFrame url="app.phantomhire.com/projects/vp-engineering/analytics" badge="Live now">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-foreground">Project analytics</p>
            <Badge variant="neutral" className="font-mono">
              62 candidates
            </Badge>
          </div>

          <BreakdownPanel
            label="fit_rating_breakdown"
            rows={FIT_RATING_ROWS}
            barClass={(label) =>
              "h-full rounded-full " +
              (label === "Strong Fit"
                ? "bg-success"
                : label === "Good Fit"
                  ? "bg-info"
                  : label === "Possible Fit"
                    ? "bg-warning"
                    : "bg-danger")
            }
          />

          <BreakdownPanel label="status_breakdown" rows={STATUS_ROWS} barClass={() => "h-full rounded-full bg-brand"} />

          <BreakdownPanel label="source_breakdown" rows={SOURCE_ROWS} barClass={() => "h-full rounded-full bg-electric"} />
        </div>
      </BrowserFrame>
    </div>
  );
}
