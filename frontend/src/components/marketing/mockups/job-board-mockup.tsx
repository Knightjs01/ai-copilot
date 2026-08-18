import Image from "next/image";
import { Briefcase, Clock, EyeOff, MapPin, Search } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { CornerMarks } from "@/components/marketing/mockups/corner-marks";

const FILTERS = ["Remote", "Engineering", "£80k+"];

const LISTINGS = [
  {
    title: "Senior Backend Engineer",
    employer: "Confidential · Series C Fintech",
    location: "Remote",
    salary: "£90k–£110k",
    type: "Full-time",
    tags: ["Payments", "Distributed systems"],
    posted: "2d ago",
  },
  {
    title: "VP of Sales",
    employer: "Confidential · Enterprise SaaS",
    location: "London · Hybrid",
    salary: "Competitive",
    type: "Full-time",
    tags: ["Enterprise SaaS", "Team building"],
    posted: "5d ago",
  },
  {
    title: "Staff Product Designer",
    employer: "Confidential · Consumer App",
    location: "Remote",
    salary: "£85k–£100k",
    type: "Contract",
    tags: ["Design systems"],
    posted: "1d ago",
  },
];

export function JobBoardMockup() {
  return (
    <div className="relative">
      <CornerMarks />
      <BrowserFrame url="jobs.phantomhire.com" badge="Live now">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <Image
              src="/shadow-wordmark.png"
              alt="Shadow — Anonymous Job Board"
              width={1525}
              height={550}
              className="h-9 w-auto sm:h-11"
              priority
            />
            <span className="hidden shrink-0 items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 text-[10px] font-medium text-muted-foreground sm:flex">
              <EyeOff className="h-3 w-3 shrink-0" />
              Anonymous by default
            </span>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2.5">
            <Search className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Search roles by skill, not by title…</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {FILTERS.map((filter) => (
              <span
                key={filter}
                className="rounded-full border border-border bg-brand/10 px-3 py-1 text-[11px] font-medium text-brand"
              >
                {filter}
              </span>
            ))}
            <span className="ml-auto font-mono text-[11px] text-muted-foreground">3 roles</span>
          </div>

          <div className="flex flex-col gap-2.5">
            {LISTINGS.map((job) => (
              <div key={job.title} className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3.5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-foreground">{job.title}</p>
                    <p className="mt-1 flex items-center gap-1 text-[11px] text-muted-foreground">
                      <EyeOff className="h-3 w-3 shrink-0" />
                      {job.employer}
                    </p>
                  </div>
                  <span className="shrink-0 rounded-full bg-success/10 px-2.5 py-1 font-mono text-[11px] font-semibold text-success">
                    {job.salary}
                  </span>
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
                  <span className="ml-auto flex items-center gap-1">
                    <Clock className="h-3 w-3 shrink-0" />
                    {job.posted}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {job.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-border bg-secondary/40 px-2 py-0.5 text-[10px] text-foreground/80"
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
    </div>
  );
}
