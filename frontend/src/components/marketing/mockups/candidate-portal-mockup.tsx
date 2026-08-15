import { EyeOff, Flame } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

const MATCHES = [
  { title: "Senior Backend Engineer", match: 92 },
  { title: "Staff Platform Engineer", match: 87 },
];

export function CandidatePortalMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/passport" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-3.5">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand/10 text-xs font-semibold text-brand">
            P-78
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">Pulse-78</p>
            <p className="flex items-center gap-1 text-[11px] text-muted-foreground">
              <EyeOff className="h-3 w-3 shrink-0" />
              Identity hidden, reveal only when you choose
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-xl border border-border bg-card p-3.5">
          <Flame className="h-4 w-4 shrink-0 text-brand" />
          <p className="text-xs leading-relaxed text-muted-foreground">
            <span className="font-medium text-foreground">Zero-Retention. </span>
            Your data is purged the moment the search closes.
          </p>
        </div>

        <div className="flex flex-col gap-2.5">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Matched to you
          </p>
          {MATCHES.map((role) => (
            <div
              key={role.title}
              className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card p-3.5"
            >
              <p className="text-sm font-medium text-foreground">{role.title}</p>
              <span className="shrink-0 rounded-full bg-success/10 px-2.5 py-1 text-[11px] font-semibold text-success">
                {role.match}% match
              </span>
            </div>
          ))}
        </div>
      </div>
    </BrowserFrame>
  );
}
