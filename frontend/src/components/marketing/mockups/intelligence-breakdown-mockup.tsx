import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { Badge } from "@/components/ui/badge";

// Mirrors the real ProjectAnalytics shape (status/fit_rating/source breakdowns, all computed
// within a single project) — illustrative sample numbers, same convention as every other
// mockup on this site, not fictional market data.
const FIT_RATING_ROWS = [
  { label: "Strong Fit", value: 34, variant: "success" as const },
  { label: "Good Fit", value: 28, variant: "info" as const },
  { label: "Possible Fit", value: 22, variant: "warning" as const },
  { label: "Weak Fit", value: 16, variant: "danger" as const },
];

const STATUS_ROWS = [
  { label: "Screening", value: 41 },
  { label: "Interviewing", value: 24 },
  { label: "Offer", value: 9 },
];

export function IntelligenceBreakdownMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/projects/vp-engineering/analytics" badge="Live now">
      <div className="flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-foreground">Project analytics</p>
          <Badge variant="neutral">62 candidates</Badge>
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            fit_rating_breakdown
          </p>
          {FIT_RATING_ROWS.map((row) => (
            <div key={row.label} className="flex items-center gap-2.5">
              <span className="w-24 shrink-0 text-xs text-foreground/80">{row.label}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary/60">
                <div
                  className={
                    row.variant === "success"
                      ? "h-full rounded-full bg-success"
                      : row.variant === "info"
                        ? "h-full rounded-full bg-info"
                        : row.variant === "warning"
                          ? "h-full rounded-full bg-warning"
                          : "h-full rounded-full bg-danger"
                  }
                  style={{ width: `${row.value}%` }}
                />
              </div>
              <span className="w-8 shrink-0 text-right text-xs text-muted-foreground">
                {row.value}%
              </span>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            status_breakdown
          </p>
          {STATUS_ROWS.map((row) => (
            <div key={row.label} className="flex items-center gap-2.5">
              <span className="w-24 shrink-0 text-xs text-foreground/80">{row.label}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary/60">
                <div className="h-full rounded-full bg-brand" style={{ width: `${row.value}%` }} />
              </div>
              <span className="w-8 shrink-0 text-right text-xs text-muted-foreground">
                {row.value}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </BrowserFrame>
  );
}
