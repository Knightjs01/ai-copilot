import {
  CheckCircle2,
  HelpCircle,
  LayoutGrid,
  Lock,
  ShieldCheck,
  TriangleAlert,
  UserCog,
  Users,
} from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { Badge } from "@/components/ui/badge";

// A denser "full app shell" view than the compact dashboard/kanban mockups used elsewhere on
// this page — sidebar, top bar, kanban, and a real AI fit-assessment panel, all real data
// shapes (CANDIDATE_STATUS_LABEL, FitRating, PrescreenAssessment). No candidate photos (identity
// stays Callsign-only until reveal), no numeric match score, no audio/transcript — the real
// product doesn't have any of those. Illustrative sample data, same convention as every other
// mockup on this site.
const SIDEBAR_ITEMS = [
  { label: "Dashboard", active: true },
  { label: "Projects", active: false },
  { label: "Candidates", active: false },
  { label: "Shadow Jobs", active: false },
  { label: "Team", active: false },
  { label: "Security", active: false },
];

const COLUMNS = [
  {
    stage: "Screening",
    cards: [
      { callsign: "Echo-14", fit: "Good Fit", variant: "info" as const },
      { callsign: "Nova-32", fit: "Possible Fit", variant: "warning" as const },
    ],
  },
  {
    stage: "Interviewing",
    cards: [{ callsign: "Cipher-05", fit: "Strong Fit", variant: "success" as const }],
  },
  {
    stage: "Offer",
    cards: [{ callsign: "Atlas-91", fit: "Strong Fit", variant: "success" as const }],
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

        <div className="flex min-w-0 flex-1 flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-foreground">VP Engineering</p>
              <p className="text-[11px] text-muted-foreground">Engineering · Open role</p>
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

          <div className="grid grid-cols-3 gap-3">
            {COLUMNS.map((column) => (
              <div key={column.stage} className="flex flex-col gap-2">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                  {column.stage}
                </p>
                <div className="flex flex-col gap-2">
                  {column.cards.map((card) => (
                    <div
                      key={card.callsign}
                      className="flex flex-col gap-2 rounded-xl border border-border bg-card p-2.5"
                    >
                      <p className="truncate text-xs font-medium text-foreground">
                        {card.callsign}
                      </p>
                      <Badge variant={card.variant} className="w-fit text-[10px]">
                        {card.fit}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3">
            <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              <ShieldCheck className="h-3.5 w-3.5 text-brand" />
              AI fit assessment · Cipher-05
            </p>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <div className="flex items-start gap-1.5 rounded-lg bg-success/5 p-2">
                <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-success" />
                <p className="text-[11px] text-foreground/80">
                  Led a payments platform at scale
                </p>
              </div>
              <div className="flex items-start gap-1.5 rounded-lg bg-warning/5 p-2">
                <TriangleAlert className="mt-0.5 h-3 w-3 shrink-0 text-warning" />
                <p className="text-[11px] text-foreground/80">
                  Team-size ownership unconfirmed
                </p>
              </div>
              <div className="flex items-start gap-1.5 rounded-lg bg-secondary/40 p-2">
                <HelpCircle className="mt-0.5 h-3 w-3 shrink-0 text-muted-foreground" />
                <p className="text-[11px] text-foreground/80">Ask: team size you led?</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <Lock className="h-3 w-3" />
              Identity locked
            </span>
            <span className="flex items-center gap-1">
              <UserCog className="h-3 w-3" />
              Owner-only reveal
            </span>
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" />3 teammates
            </span>
          </div>
        </div>
      </div>
    </BrowserFrame>
  );
}
