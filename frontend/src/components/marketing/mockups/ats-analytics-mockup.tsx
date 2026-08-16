import { CheckCircle2, Clock, MessageSquareText, Users } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

// Real ProjectAnalytics breakdown fields (status_breakdown/fit_rating_breakdown) paired with the
// real ActionItem mechanic (4 real action types). Illustrative sample data, same convention as
// every other mockup on this site.
const FIT_RATING_ROWS = [
  { label: "Strong Fit", value: 34, variant: "success" as const },
  { label: "Good Fit", value: 28, variant: "info" as const },
  { label: "Possible Fit", value: 22, variant: "warning" as const },
];

const ACTION_ITEMS = [
  { icon: CheckCircle2, message: "Cipher-05 is ready to advance to Interviewing" },
  { icon: Clock, message: "Atlas-91 needs an interview scheduled" },
  { icon: MessageSquareText, message: "Nova-32 needs a prescreen assessment" },
  { icon: Users, message: "VP Engineering needs hiring manager alignment" },
];

export function AtsAnalyticsMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/projects/vp-engineering/analytics" badge="Live now">
      <div className="flex flex-col gap-5">
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
                        : "h-full rounded-full bg-warning"
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
            What needs your attention
          </p>
          {ACTION_ITEMS.map((item) => (
            <div
              key={item.message}
              className="flex items-center gap-2.5 rounded-lg border border-border bg-card p-2.5"
            >
              <item.icon className="h-3.5 w-3.5 shrink-0 text-brand" />
              <p className="text-xs text-foreground">{item.message}</p>
            </div>
          ))}
        </div>
      </div>
    </BrowserFrame>
  );
}
