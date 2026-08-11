import { EyeOff, Search } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

const FILTERS = ["Remote", "Engineering", "£80k+"];

const LISTINGS = [
  {
    title: "Senior Backend Engineer",
    meta: "Remote · £90k–£110k",
    employer: "Confidential — Series C Fintech",
  },
  {
    title: "VP of Sales",
    meta: "London · Competitive",
    employer: "Confidential — Enterprise SaaS",
  },
  {
    title: "Staff Product Designer",
    meta: "Remote · £85k–£100k",
    employer: "Confidential — Consumer App",
  },
];

export function JobBoardMockup() {
  return (
    <BrowserFrame url="jobs.phantomhire.com" badge="Coming soon">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 rounded-full border border-border bg-white px-4 py-2.5">
          <Search className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">Search roles by skill, not by title…</span>
        </div>

        <div className="flex flex-wrap gap-2">
          {FILTERS.map((filter) => (
            <span
              key={filter}
              className="rounded-full border border-border bg-white px-3 py-1 text-[11px] text-foreground"
            >
              {filter}
            </span>
          ))}
        </div>

        <div className="flex flex-col gap-2.5">
          {LISTINGS.map((job) => (
            <div
              key={job.title}
              className="flex items-center justify-between gap-3 rounded-xl border border-border bg-white p-3.5"
            >
              <div>
                <p className="text-sm font-medium text-foreground">{job.title}</p>
                <p className="text-xs text-muted-foreground">{job.meta}</p>
                <p className="mt-1 flex items-center gap-1 text-[11px] text-muted-foreground">
                  <EyeOff className="h-3 w-3 shrink-0" />
                  {job.employer}
                </p>
              </div>
              <span className="shrink-0 rounded-full bg-brand/10 px-3 py-1 text-[11px] font-medium text-brand">
                View role
              </span>
            </div>
          ))}
        </div>
      </div>
    </BrowserFrame>
  );
}
