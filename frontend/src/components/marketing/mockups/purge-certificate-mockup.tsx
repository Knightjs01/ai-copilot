import { CheckCircle2, Flame } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

const CATEGORIES_DESTROYED = [
  "Uploaded resumes",
  "Sanitized CVs",
  "AI candidate intelligence",
  "Candidate identity vault records",
  "Candidate records",
];

export function PurgeCertificateMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/historic-vault" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-3.5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
            <Flame className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Senior Backend Engineer</p>
            <p className="text-xs text-muted-foreground">
              Purged by owner@company.com · 2 candidates
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-3.5">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Destroyed
          </p>
          <ul className="mt-2 flex flex-col gap-1.5">
            {CATEGORIES_DESTROYED.map((category) => (
              <li key={category} className="flex items-center gap-1.5 text-xs text-foreground">
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success" />
                {category}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-[11px] text-muted-foreground">
          Certificate ID: PC-2026-0912 · Stored in the Historic Vault
        </p>
      </div>
    </BrowserFrame>
  );
}
