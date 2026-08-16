import { EyeOff, Vault } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { Badge } from "@/components/ui/badge";
import { VERIFICATION_STATUS_LABEL, VERIFICATION_STATUS_VARIANT } from "@/lib/status-display";

// A fuller "document" view than the homepage's compact teaser (passport-mockup.tsx) — the
// flagship visual for the dedicated /passport page. Every field mirrors PhantomPassport's real
// shape (headline/seniority/skills/completion_percentage/verification_status/career_entries with
// their real dual company_name / company_name_anonymized mechanic). Illustrative sample data,
// same convention as every other mockup on this site.
const SKILLS = ["Distributed Systems", "Go", "Platform Architecture", "Kubernetes"];

const CAREER_ENTRIES = [
  { title: "Staff Engineer", anonymized: "Series C Fintech", current: true },
  { title: "Senior Backend Engineer", anonymized: "Enterprise SaaS", current: false },
];

export function PassportDetailMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/passport" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-brand/60 text-sm font-semibold text-brand">
            P-78
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-foreground">Pulse-78</p>
            <p className="truncate text-xs text-muted-foreground">
              Senior Backend Engineer · Remote · 6 yrs experience
            </p>
          </div>
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 border-brand/40">
            <span className="text-xs font-semibold text-brand">92%</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant={VERIFICATION_STATUS_VARIANT.pending}>
            {VERIFICATION_STATUS_LABEL.pending}
          </Badge>
          <Badge variant="neutral">92% complete</Badge>
        </div>

        <div className="flex flex-wrap gap-2">
          {SKILLS.map((skill) => (
            <span
              key={skill}
              className="rounded-full border border-border bg-card px-3 py-1 text-[11px] text-foreground/80"
            >
              {skill}
            </span>
          ))}
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Career history
          </p>
          {CAREER_ENTRIES.map((entry) => (
            <div
              key={entry.title}
              className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card p-3"
            >
              <div className="min-w-0">
                <p className="truncate text-xs font-medium text-foreground">{entry.title}</p>
                <p className="truncate text-[11px] text-muted-foreground">{entry.anonymized}</p>
              </div>
              <span className="flex shrink-0 items-center gap-1 text-[10px] text-muted-foreground">
                <EyeOff className="h-3 w-3" />
                Real employer hidden
              </span>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card p-3.5">
          <div className="flex items-center gap-2.5">
            <Vault className="h-4 w-4 shrink-0 text-brand" />
            <p className="text-sm font-medium text-foreground">Candidate Vault</p>
          </div>
          <span className="shrink-0 rounded-full bg-brand/10 px-2.5 py-1 text-[11px] font-semibold text-brand">
            Approved · Version 3
          </span>
        </div>
      </div>
    </BrowserFrame>
  );
}
