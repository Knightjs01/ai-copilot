import { Badge } from "@/components/ui/badge";
import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

const DASHBOARD_STATS = [
  { label: "Live projects", value: "3" },
  { label: "Candidates in process", value: "14" },
  { label: "Pre-screen stage", value: "5" },
  { label: "Hiring manager stage", value: "3" },
];

// Fit ratings mirror the real 4-value FitRating type — no invented score, just the real
// color-coded system this page goes on to explain.
const CANDIDATES = [
  { callsign: "Cipher-05", stage: "Interviewing", fit: "Strong Fit", variant: "success" as const },
  { callsign: "Echo-14", stage: "Screening", fit: "Good Fit", variant: "info" as const },
  { callsign: "Nova-32", stage: "Screening", fit: "Possible Fit", variant: "warning" as const },
  { callsign: "Atlas-91", stage: "Offer", fit: "Strong Fit", variant: "success" as const },
];

export function AtsDashboardMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/projects/vp-engineering" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-foreground">VP Engineering</p>
            <p className="text-xs text-muted-foreground">Engineering · Open role</p>
          </div>
          <span className="rounded-full bg-info/10 px-2.5 py-1 text-xs font-medium text-info">
            87 candidates
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {DASHBOARD_STATS.map((stat) => (
            <div key={stat.label} className="rounded-xl border border-border bg-card px-3 py-2.5">
              <p className="text-lg font-semibold leading-none text-foreground">{stat.value}</p>
              <p className="mt-1 text-[11px] leading-tight text-muted-foreground">{stat.label}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            AI fit rating
          </p>
          {CANDIDATES.map((candidate) => (
            <div
              key={candidate.callsign}
              className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card p-2.5"
            >
              <div className="flex items-center gap-2.5">
                <span className="text-xs font-medium text-foreground">{candidate.callsign}</span>
                <span className="text-[11px] text-muted-foreground">{candidate.stage}</span>
              </div>
              <Badge variant={candidate.variant}>{candidate.fit}</Badge>
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-brand/20 bg-brand/5 p-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-brand">
            Phantom AI insight
          </p>
          <p className="mt-1 text-xs text-foreground">
            Two candidates meet every hiring-manager priority for this role.
          </p>
        </div>
      </div>
    </BrowserFrame>
  );
}
