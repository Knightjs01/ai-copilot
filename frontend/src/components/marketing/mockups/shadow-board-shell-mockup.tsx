import { Briefcase, MapPin, Search } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { Badge } from "@/components/ui/badge";

// Denser board mockup than the homepage's JobBoardMockup teaser — real filter chips
// (seniority/remote/employment type, matching the real useShadowBoard() backend params) and
// richer listing cards (salary, location, employment type, requirement tags), same real fields
// as the live /shadow board (ShadowJobBoardListing). Illustrative sample data, same convention
// as every mockup on this site.
const FILTERS = ["Senior", "Remote", "Full-time"];

const LISTINGS = [
  {
    title: "Senior Backend Engineer",
    company: "Confidential · Series C Fintech",
    location: "Remote",
    salary: "£90k – £110k",
    type: "Full-time",
    tags: ["Payments", "Distributed systems"],
  },
  {
    title: "VP of Sales",
    company: "Confidential · Enterprise SaaS",
    location: "London · Hybrid",
    salary: "Competitive",
    type: "Full-time",
    tags: ["Enterprise SaaS", "Team building"],
  },
  {
    title: "Staff Product Designer",
    company: "Confidential · Consumer App",
    location: "Remote",
    salary: "£85k – £100k",
    type: "Contract",
    tags: ["Design systems"],
  },
];

export function ShadowBoardShellMockup() {
  return (
    <BrowserFrame url="jobs.phantomhire.com" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2.5">
          <Search className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">Search roles by skill, not by title…</span>
        </div>

        <div className="flex flex-wrap gap-2">
          {FILTERS.map((filter) => (
            <span
              key={filter}
              className="rounded-full border border-border bg-brand/10 px-3 py-1 text-[11px] font-medium text-brand"
            >
              {filter}
            </span>
          ))}
          <span className="text-[11px] text-muted-foreground">3 roles</span>
        </div>

        <div className="flex flex-col gap-2.5">
          {LISTINGS.map((job) => (
            <div key={job.title} className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3.5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-foreground">{job.title}</p>
                  <p className="text-xs text-muted-foreground">{job.company}</p>
                </div>
                <Badge variant="success" className="shrink-0">
                  {job.salary}
                </Badge>
              </div>
              <div className="flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <MapPin className="h-3 w-3 shrink-0" />
                  {job.location}
                </span>
                <span className="flex items-center gap-1">
                  <Briefcase className="h-3 w-3 shrink-0" />
                  {job.type}
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {job.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full border border-border bg-secondary/40 px-2.5 py-0.5 text-[11px] text-foreground/80"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </BrowserFrame>
  );
}
