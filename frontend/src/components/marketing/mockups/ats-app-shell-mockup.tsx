import {
  Archive,
  Briefcase,
  Check,
  ChevronLeft,
  ChevronRight,
  Eye,
  Home,
  MessageSquare,
  MoreHorizontal,
  Plus,
  Settings,
  Shield,
  StickyNote,
  TriangleAlert,
  Users,
  Vault,
  X,
} from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { Badge } from "@/components/ui/badge";
import {
  CANDIDATE_SOURCE_LABEL,
  CANDIDATE_STATUS_LABEL,
  CANDIDATE_STATUS_VARIANT,
  FIT_RATING_VARIANT,
} from "@/lib/status-display";
import type { CandidateSource, CandidateStatus, FitRating } from "@/lib/types";

// A dense, full "app shell" hero visual — sidebar, project header, tab bar, stat row, 5-column
// kanban, candidate table, three insight panels, and a candidate detail drawer. Every status
// column, badge variant, and label comes from the real CANDIDATE_STATUS/FIT_RATING/CANDIDATE_SOURCE
// maps. No numeric "AI match %" anywhere — the real product only ever computes the 4-tier FitRating
// (Strong/Good/Possible/Weak Fit), never a percentage, so every "match" here is that real label, not
// an invented score. The gold "Verified" badge mirrors the same real single-state verification
// treatment used on the Passport card (decorative gold, not a graded tier). "Requirements coverage"
// reuses the real Hiring Manager Alignment / top_requirements concept explained on this page's own
// Alignment section, not a fabricated skills-match percentage. "Candidate source" reuses the real
// ProjectAnalytics.source_breakdown concept. Illustrative sample data throughout, same convention as
// every mockup on this site.

const SIDEBAR_WORK = [
  { icon: Briefcase, label: "Projects", active: true },
  { icon: Users, label: "Candidates", active: false },
  { icon: Shield, label: "Team", active: false },
];

const SIDEBAR_DATA = [
  { icon: Vault, label: "Project Vault", active: false },
  { icon: Archive, label: "Historic Vault", active: false },
];

const TABS = ["Overview", "Pipeline", "Candidates", "AI insights", "Analytics"];

const STATUS_ORDER: CandidateStatus[] = ["new", "screening", "interviewing", "offer", "hired"];

const KANBAN: Record<
  CandidateStatus,
  { count: number; cards: { callsign: string; fit: FitRating; reviewer: string }[] }
> = {
  new: {
    count: 34,
    cards: [
      { callsign: "Echo-14", fit: "Good Fit", reviewer: "J" },
      { callsign: "Nova-32", fit: "Possible Fit", reviewer: "A" },
    ],
  },
  screening: {
    count: 22,
    cards: [
      { callsign: "Cipher-05", fit: "Strong Fit", reviewer: "R" },
      { callsign: "Wraith-9", fit: "Good Fit", reviewer: "J" },
    ],
  },
  interviewing: {
    count: 18,
    cards: [
      { callsign: "Spectre-482", fit: "Strong Fit", reviewer: "J" },
      { callsign: "Atlas-91", fit: "Strong Fit", reviewer: "A" },
    ],
  },
  offer: {
    count: 3,
    cards: [{ callsign: "Halcyon-6", fit: "Strong Fit", reviewer: "R" }],
  },
  hired: { count: 1, cards: [] },
  rejected: { count: 0, cards: [] },
  withdrawn: { count: 0, cards: [] },
};

const FIT_LEGEND: { fit: FitRating; count: number }[] = [
  { fit: "Strong Fit", count: 9 },
  { fit: "Good Fit", count: 14 },
  { fit: "Possible Fit", count: 11 },
  { fit: "Weak Fit", count: 3 },
];

const TABLE_ROWS: {
  callsign: string;
  role: string;
  fit: FitRating;
  status: CandidateStatus;
  activity: string;
  manager: string;
  tags: string[];
}[] = [
  {
    callsign: "Spectre-482",
    role: "Senior Product Leader",
    fit: "Strong Fit",
    status: "interviewing",
    activity: "2h ago",
    manager: "Jane Cooper",
    tags: ["Fintech", "Payments"],
  },
  {
    callsign: "Halcyon-6",
    role: "VP Product",
    fit: "Strong Fit",
    status: "offer",
    activity: "5h ago",
    manager: "Robert Fox",
    tags: ["SaaS", "Leadership"],
  },
  {
    callsign: "Atlas-91",
    role: "Head of Engineering",
    fit: "Strong Fit",
    status: "interviewing",
    activity: "1d ago",
    manager: "Jane Cooper",
    tags: ["Engineering", "Scale"],
  },
  {
    callsign: "Wraith-9",
    role: "Engineering Director",
    fit: "Good Fit",
    status: "screening",
    activity: "2d ago",
    manager: "Robert Fox",
    tags: ["Cloud", "Leadership"],
  },
];

const REQUIREMENTS_COVERAGE = [
  { text: "Owned a production payments platform", coverage: 90 },
  { text: "Led distributed engineering teams", coverage: 75 },
  { text: "Scaled an org past 30 people", coverage: 55 },
];

const SOURCE_BREAKDOWN: { source: CandidateSource; pct: number }[] = [
  { source: "referral", pct: 40 },
  { source: "job_board", pct: 27 },
  { source: "agency", pct: 18 },
  { source: "direct", pct: 10 },
  { source: "other", pct: 5 },
];

const STRENGTHS = [
  { text: "Payments infrastructure", strong: true },
  { text: "Product leadership", strong: true },
  { text: "Strategic ownership", strong: false },
];

function GoldVerifiedBadge() {
  return (
    <span className="flex items-center gap-1 rounded-full border border-[#d4af6a]/50 bg-[#d4af6a]/10 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-[#8a6a1f]">
      <span className="flex h-3 w-3 items-center justify-center rounded-full bg-[#d4af6a]">
        <Check className="h-2 w-2 text-[#100b1f]" strokeWidth={4} />
      </span>
      Verified
    </span>
  );
}

export function AtsAppShellMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/projects/vp-engineering" badge="Live now">
      <div className="flex gap-4 overflow-x-auto">
        <div className="hidden w-36 shrink-0 flex-col gap-4 border-r border-border pr-3 sm:flex">
          <span className="flex items-center gap-1.5 text-[11px] font-semibold text-foreground">
            <Home className="h-3.5 w-3.5 text-brand" />
            Home
          </span>

          <div className="flex flex-col gap-1">
            <p className="px-1 text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
              Work
            </p>
            {SIDEBAR_WORK.map((item) => (
              <span
                key={item.label}
                className={
                  item.active
                    ? "flex items-center gap-1.5 rounded-lg bg-brand/10 px-2 py-1.5 text-[11px] font-medium text-brand"
                    : "flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[11px] text-muted-foreground"
                }
              >
                <item.icon className="h-3 w-3 shrink-0" />
                {item.label}
              </span>
            ))}
          </div>

          <div className="flex flex-col gap-1">
            <p className="px-1 text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
              Data
            </p>
            {SIDEBAR_DATA.map((item) => (
              <span
                key={item.label}
                className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[11px] text-muted-foreground"
              >
                <item.icon className="h-3 w-3 shrink-0" />
                {item.label}
              </span>
            ))}
          </div>

          <span className="mt-auto flex items-center gap-1.5 px-2 text-[11px] text-muted-foreground">
            <Settings className="h-3 w-3 shrink-0" />
            Settings
          </span>
        </div>

        <div className="flex min-w-[560px] flex-1 flex-col gap-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <ChevronLeft className="h-3 w-3" />
                Back to projects
              </p>
              <div className="mt-1 flex items-center gap-2">
                <p className="text-base font-semibold text-foreground">VP Engineering</p>
                <Badge variant="success">Open</Badge>
              </div>
              <p className="mt-0.5 text-[10px] text-muted-foreground">
                London, UK · Full-time · £140k–£180k · Created 12 days ago
              </p>
            </div>
            <span className="flex shrink-0 items-center gap-1 rounded-full bg-brand px-2.5 py-1.5 text-[10px] font-medium text-brand-foreground">
              <Plus className="h-3 w-3" />
              Add candidate
            </span>
          </div>

          <div className="flex items-center gap-3 border-b border-border pb-1.5">
            {TABS.map((tab, index) => (
              <span
                key={tab}
                className={
                  index === 1
                    ? "border-b-2 border-brand pb-1.5 text-[10px] font-semibold text-foreground"
                    : "pb-1.5 text-[10px] text-muted-foreground"
                }
              >
                {tab}
              </span>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-4 rounded-xl border border-border bg-card p-3">
            {[
              { label: "Total candidates", value: "78" },
              { label: "Strong matches", value: "9" },
              { label: "Interviewing", value: "18" },
              { label: "Offer", value: "3" },
              { label: "Hired", value: "1" },
            ].map((stat) => (
              <div key={stat.label} className="flex flex-col gap-0.5">
                <p className="text-sm font-bold text-foreground">{stat.value}</p>
                <p className="text-[9px] text-muted-foreground">{stat.label}</p>
              </div>
            ))}
            <div className="ml-auto flex items-center gap-2">
              {FIT_LEGEND.map((item) => (
                <span key={item.fit} className="flex items-center gap-1 text-[9px] text-muted-foreground">
                  <Badge variant={FIT_RATING_VARIANT[item.fit]} className="px-1.5 py-0 text-[8px]">
                    {item.count}
                  </Badge>
                  {item.fit.replace(" Fit", "")}
                </span>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-5 gap-2">
            {STATUS_ORDER.map((status) => (
              <div key={status} className="flex flex-col gap-1.5">
                <div className="flex items-baseline justify-between">
                  <p className="text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {CANDIDATE_STATUS_LABEL[status]}
                  </p>
                  <span className="text-[9px] font-semibold text-muted-foreground">
                    {KANBAN[status].count}
                  </span>
                </div>
                <div className="flex flex-col gap-1.5">
                  {KANBAN[status].cards.map((card) => (
                    <div
                      key={card.callsign}
                      className="flex flex-col gap-1 rounded-lg border border-border bg-card p-2"
                    >
                      <div className="flex items-center justify-between gap-1">
                        <p className="truncate text-[10px] font-medium text-foreground">
                          {card.callsign}
                        </p>
                        <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-secondary text-[8px] font-semibold text-foreground">
                          {card.reviewer}
                        </span>
                      </div>
                      <Badge variant={FIT_RATING_VARIANT[card.fit]} className="w-fit px-1.5 py-0 text-[8px]">
                        {card.fit}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="overflow-hidden rounded-xl border border-border">
            <table className="w-full text-left">
              <thead className="bg-secondary/40">
                <tr>
                  {["Candidate", "Fit", "Stage", "Activity", "Manager", "Tags"].map((h) => (
                    <th
                      key={h}
                      className="px-2.5 py-1.5 text-[9px] font-semibold uppercase tracking-wide text-muted-foreground"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {TABLE_ROWS.map((row) => (
                  <tr key={row.callsign} className="border-t border-border">
                    <td className="px-2.5 py-1.5">
                      <p className="text-[10px] font-medium text-foreground">{row.callsign}</p>
                      <p className="text-[9px] text-muted-foreground">{row.role}</p>
                    </td>
                    <td className="px-2.5 py-1.5">
                      <Badge variant={FIT_RATING_VARIANT[row.fit]} className="px-1.5 py-0 text-[8px]">
                        {row.fit}
                      </Badge>
                    </td>
                    <td className="px-2.5 py-1.5">
                      <Badge variant={CANDIDATE_STATUS_VARIANT[row.status]} className="px-1.5 py-0 text-[8px]">
                        {CANDIDATE_STATUS_LABEL[row.status]}
                      </Badge>
                    </td>
                    <td className="px-2.5 py-1.5 text-[9px] text-muted-foreground">{row.activity}</td>
                    <td className="px-2.5 py-1.5 text-[9px] text-muted-foreground">{row.manager}</td>
                    <td className="px-2.5 py-1.5">
                      <div className="flex gap-1">
                        {row.tags.map((tag) => (
                          <span
                            key={tag}
                            className="rounded-full border border-border bg-secondary/40 px-1.5 py-0.5 text-[8px] text-foreground/80"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3">
              <p className="text-[10px] font-semibold text-foreground">AI insight</p>
              <p className="text-[9px] leading-relaxed text-muted-foreground">
                3 candidates meet every hiring-manager priority. Consider moving Spectre-482 to
                Offer.
              </p>
              <span className="text-[9px] font-medium text-brand">View all insights →</span>
            </div>

            <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3">
              <p className="text-[10px] font-semibold text-foreground">Requirements coverage</p>
              <div className="flex flex-col gap-1.5">
                {REQUIREMENTS_COVERAGE.map((req) => (
                  <div key={req.text} className="flex flex-col gap-0.5">
                    <p className="text-[8px] text-muted-foreground">{req.text}</p>
                    <div className="h-1 w-full overflow-hidden rounded-full bg-secondary">
                      <div
                        className="h-full rounded-full bg-brand"
                        style={{ width: `${req.coverage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3">
              <p className="text-[10px] font-semibold text-foreground">Candidate source</p>
              <div className="flex flex-col gap-1">
                {SOURCE_BREAKDOWN.map((item) => (
                  <div key={item.source} className="flex items-center justify-between gap-2">
                    <span className="text-[8px] text-muted-foreground">
                      {CANDIDATE_SOURCE_LABEL[item.source]}
                    </span>
                    <div className="flex flex-1 items-center gap-1.5">
                      <div className="h-1 flex-1 overflow-hidden rounded-full bg-secondary">
                        <div
                          className="h-full rounded-full bg-brand/70"
                          style={{ width: `${item.pct}%` }}
                        />
                      </div>
                      <span className="w-6 shrink-0 text-right text-[8px] text-muted-foreground">
                        {item.pct}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="hidden w-64 shrink-0 flex-col gap-3 border-l border-border pl-3 lg:flex">
          <div className="flex items-center justify-between text-[9px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <ChevronLeft className="h-3 w-3" />
              Previous
            </span>
            <span className="flex items-center gap-1">
              Next
              <ChevronRight className="h-3 w-3" />
            </span>
          </div>

          <div className="flex flex-col items-center gap-2 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full border-2 border-brand/40 bg-brand/10 text-sm font-semibold text-brand">
              S-482
            </div>
            <GoldVerifiedBadge />
            <p className="text-xs font-semibold text-foreground">Spectre-482</p>
            <p className="text-[9px] text-muted-foreground">Senior Product Leader</p>
            <div className="flex flex-wrap justify-center gap-1">
              {["Fintech", "Payments", "SaaS"].map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-border bg-secondary/40 px-1.5 py-0.5 text-[8px] text-foreground/80"
                >
                  {tag}
                </span>
              ))}
            </div>
            <p className="text-[9px] text-muted-foreground">London, UK · 12 yrs experience</p>
          </div>

          <div className="flex flex-col items-center gap-1 rounded-xl border border-border bg-card p-3 text-center">
            <Badge variant={FIT_RATING_VARIANT["Strong Fit"]}>Strong Fit</Badge>
            <p className="text-[9px] leading-relaxed text-muted-foreground">
              Exceptional evidence of payments-platform ownership and cross-functional leadership
              at scale.
            </p>
          </div>

          <div className="flex items-center justify-between text-[8px] text-muted-foreground">
            <span>Stage: Interviewing</span>
            <span>2h ago</span>
          </div>

          <div className="flex items-center justify-between">
            {[
              { icon: MessageSquare, label: "Message" },
              { icon: Eye, label: "Reveal" },
              { icon: StickyNote, label: "Note" },
              { icon: MoreHorizontal, label: "More" },
            ].map((action) => (
              <span
                key={action.label}
                className="flex flex-col items-center gap-1 text-[8px] text-muted-foreground"
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-full border border-border bg-card">
                  <action.icon className="h-3 w-3" />
                </span>
                {action.label}
              </span>
            ))}
          </div>

          <div className="flex flex-col gap-1.5 rounded-xl border border-border bg-card p-3">
            <p className="text-[9px] font-semibold text-foreground">AI summary</p>
            <p className="text-[9px] leading-relaxed text-muted-foreground">
              Strong systems-design background with direct payments-platform ownership. Team-size
              scope still needs confirming.
            </p>
            <span className="text-[9px] font-medium text-brand">View full assessment →</span>
          </div>

          <div className="flex flex-col gap-1.5 rounded-xl border border-border bg-card p-3">
            <p className="text-[9px] font-semibold text-foreground">Key strengths</p>
            {STRENGTHS.map((item) => (
              <div key={item.text} className="flex items-start gap-1.5">
                {item.strong ? (
                  <Check className="mt-0.5 h-3 w-3 shrink-0 text-success" />
                ) : (
                  <TriangleAlert className="mt-0.5 h-3 w-3 shrink-0 text-warning" />
                )}
                <span className="text-[9px] text-foreground/80">
                  {item.text}
                  <span className="block text-[8px] text-muted-foreground">
                    {item.strong ? "Strong evidence" : "Needs clarification"}
                  </span>
                </span>
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-1 rounded-xl border border-border bg-card p-3">
            <div className="flex items-center justify-between">
              <p className="text-[9px] font-semibold text-foreground">Jane Cooper</p>
              <X className="h-3 w-3 text-muted-foreground" />
            </div>
            <p className="text-[9px] leading-relaxed text-muted-foreground">
              Great interview. Needs deeper exploration on technical architecture decisions they
              personally owned.
            </p>
          </div>
        </div>
      </div>
    </BrowserFrame>
  );
}
