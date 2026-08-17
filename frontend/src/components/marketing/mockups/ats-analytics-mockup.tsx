import { CheckCircle2, Clock, MessageSquareText, Users } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

// Real ProjectAnalytics breakdown fields (status_breakdown/fit_rating_breakdown) paired with the
// real ActionItem mechanic (4 real action types). Illustrative sample data, same convention as
// every other mockup on this site.
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

const ACTION_ITEMS = [
  { icon: CheckCircle2, message: "Cipher-05 is ready to advance to Interviewing", type: "ready_to_advance" },
  { icon: Clock, message: "Atlas-91 needs an interview scheduled", type: "needs_interview_scheduling" },
  { icon: MessageSquareText, message: "Nova-32 needs a prescreen assessment", type: "needs_prescreen" },
  { icon: Users, message: "VP Engineering needs hiring manager alignment", type: "needs_alignment" },
];

function BreakdownRow({
  label,
  value,
  className,
}: {
  label: string;
  value: number;
  className: string;
}) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="w-24 shrink-0 text-xs text-foreground/80">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-secondary/60">
        <div className={className} style={{ width: `${value}%` }} />
      </div>
      <span className="w-9 shrink-0 text-right font-mono text-xs tabular-nums text-muted-foreground">
        {value}%
      </span>
    </div>
  );
}

export function AtsAnalyticsMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/projects/vp-engineering/analytics" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="rounded-xl border border-border bg-card p-3.5">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            fit_rating_breakdown
          </p>
          <div className="mt-2.5 flex flex-col gap-2">
            {FIT_RATING_ROWS.map((row) => (
              <BreakdownRow
                key={row.label}
                label={row.label}
                value={row.value}
                className={
                  row.variant === "success"
                    ? "h-full rounded-full bg-success"
                    : row.variant === "info"
                      ? "h-full rounded-full bg-info"
                      : row.variant === "warning"
                        ? "h-full rounded-full bg-warning"
                        : "h-full rounded-full bg-danger"
                }
              />
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-3.5">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            status_breakdown
          </p>
          <div className="mt-2.5 flex flex-col gap-2">
            {STATUS_ROWS.map((row) => (
              <BreakdownRow key={row.label} label={row.label} value={row.value} className="h-full rounded-full bg-brand" />
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            What needs your attention
          </p>
          {ACTION_ITEMS.map((item) => (
            <div
              key={item.message}
              className="flex items-center gap-2.5 rounded-lg border border-border bg-card p-2.5"
            >
              <item.icon className="h-3.5 w-3.5 shrink-0 text-brand" />
              <p className="flex-1 text-xs text-foreground">{item.message}</p>
              <span className="shrink-0 font-mono text-[9px] text-muted-foreground/60">{item.type}</span>
            </div>
          ))}
        </div>
      </div>
    </BrowserFrame>
  );
}
