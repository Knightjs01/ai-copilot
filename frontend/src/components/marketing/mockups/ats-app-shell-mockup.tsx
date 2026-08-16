import { CheckCircle2, LayoutGrid, TriangleAlert } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { Badge } from "@/components/ui/badge";

// A dense "full app shell" view — sidebar, tab bar, kanban, and a real two-panel AI
// fit-assessment view, all real data shapes (CANDIDATE_STATUS_LABEL, FitRating,
// PrescreenAssessment). The small avatar on each card is the assigned teammate reviewing that
// candidate (real — recruiters aren't anonymous), not the candidate — candidates stay
// Callsign-only, since identity-hidden-until-reveal is the product's own core promise. No
// numeric match score (colored dot + the real FitRating label instead) and no audio/transcript
// player, since neither exists in the real product. Illustrative sample data, same convention
// as every other mockup on this site.
const SIDEBAR_ITEMS = [
  { label: "Dashboard", active: true },
  { label: "Projects", active: false },
  { label: "Candidates", active: false },
  { label: "Shadow Jobs", active: false },
  { label: "Team", active: false },
  { label: "Security", active: false },
];

const TABS = ["Pipeline", "Candidates", "Analytics", "Team"];

const DOT: Record<string, string> = {
  success: "bg-success",
  info: "bg-info",
  warning: "bg-warning",
};

const COLUMNS = [
  {
    stage: "Screening",
    count: 12,
    cards: [
      { callsign: "Echo-14", fit: "Good Fit", variant: "info" as const, reviewer: "J" },
      { callsign: "Nova-32", fit: "Possible Fit", variant: "warning" as const, reviewer: "A" },
    ],
    more: 4,
  },
  {
    stage: "Interviewing",
    count: 6,
    cards: [
      { callsign: "Cipher-05", fit: "Strong Fit", variant: "success" as const, reviewer: "R" },
      { callsign: "Wraith-9", fit: "Good Fit", variant: "info" as const, reviewer: "J" },
    ],
    more: 2,
  },
  {
    stage: "Offer",
    count: 2,
    cards: [{ callsign: "Atlas-91", fit: "Strong Fit", variant: "success" as const, reviewer: "A" }],
    more: 0,
  },
];

export function AtsAppShellMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/projects/vp-engineering" badge="Live now">
      <div className="flex gap-4">
        <div className="hidden w-32 shrink-0 flex-col gap-1 border-r border-border pr-3 sm:flex">
          <div className="mb-2 flex items-center gap-1.5">
            <LayoutGrid className="h-3.5 w-3.5 text-brand" />
            <span className="text-[11px] font-semibold text-foreground">Phantom Hire</span>
          </div>
          {SIDEBAR_ITEMS.map((item) => (
            <span
              key={item.label}
              className={
                item.active
                  ? "rounded-lg bg-brand/10 px-2 py-1.5 text-[11px] font-medium text-brand"
                  : "rounded-lg px-2 py-1.5 text-[11px] text-muted-foreground"
              }
            >
              {item.label}
            </span>
          ))}
        </div>

        <div className="flex min-w-0 flex-1 flex-col gap-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2">
              <p className="truncate text-sm font-semibold text-foreground">
                Senior Backend Engineer
              </p>
              <span className="flex shrink-0 items-center gap-1 text-[10px] font-medium text-success">
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                Active
              </span>
            </div>
            <div className="flex shrink-0 items-center gap-1.5">
              <div className="flex -space-x-1.5">
                {["A", "J", "R"].map((initial) => (
                  <span
                    key={initial}
                    className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-card bg-secondary text-[10px] font-semibold text-foreground"
                  >
                    {initial}
                  </span>
                ))}
              </div>
              <span className="rounded-full border border-border bg-card px-2.5 py-1 text-[10px] font-medium text-foreground">
                Invite
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 border-b border-border pb-1.5">
            {TABS.map((tab, index) => (
              <span
                key={tab}
                className={
                  index === 0
                    ? "border-b-2 border-brand pb-1.5 text-[11px] font-semibold text-foreground"
                    : "pb-1.5 text-[11px] text-muted-foreground"
                }
              >
                {tab}
              </span>
            ))}
          </div>

          <div className="grid grid-cols-3 gap-3">
            {COLUMNS.map((column) => (
              <div key={column.stage} className="flex flex-col gap-2">
                <div className="flex items-baseline justify-between">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {column.stage}
                  </p>
                  <span className="text-[10px] font-semibold text-muted-foreground">
                    {column.count}
                  </span>
                </div>
                <div className="flex flex-col gap-2">
                  {column.cards.map((card) => (
                    <div
                      key={card.callsign}
                      className="flex items-center justify-between gap-2 rounded-xl border border-border bg-card p-2.5"
                    >
                      <div className="flex min-w-0 flex-col gap-1.5">
                        <p className="truncate text-xs font-medium text-foreground">
                          {card.callsign}
                        </p>
                        <span className="flex w-fit items-center gap-1 text-[10px] text-foreground/70">
                          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${DOT[card.variant]}`} />
                          {card.fit}
                        </span>
                      </div>
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-secondary text-[9px] font-semibold text-foreground">
                        {card.reviewer}
                      </span>
                    </div>
                  ))}
                  {column.more > 0 && (
                    <p className="text-center text-[10px] text-muted-foreground">
                      +{column.more} more
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3">
              <p className="text-[11px] font-semibold text-foreground">AI fit assessment</p>
              <p className="text-[10px] text-muted-foreground">Cipher-05 · Strong Fit</p>
              <div className="mt-1 flex flex-col gap-1.5">
                <div className="flex items-start gap-1.5">
                  <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-success" />
                  <p className="text-[11px] text-foreground/80">
                    Led a payments platform scaling to £50m+ volume
                  </p>
                </div>
                <div className="flex items-start gap-1.5">
                  <TriangleAlert className="mt-0.5 h-3 w-3 shrink-0 text-warning" />
                  <p className="text-[11px] text-foreground/80">
                    Team-size ownership unconfirmed
                  </p>
                </div>
              </div>
            </div>
            <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3">
              <p className="text-[11px] font-semibold text-foreground">Summary</p>
              <p className="text-[11px] leading-relaxed text-muted-foreground">
                Strong systems-design background with direct payments-platform ownership.
                Team-size scope still needs confirming.
              </p>
              <span className="text-[10px] font-medium text-brand">View full assessment →</span>
            </div>
          </div>
        </div>
      </div>
    </BrowserFrame>
  );
}
