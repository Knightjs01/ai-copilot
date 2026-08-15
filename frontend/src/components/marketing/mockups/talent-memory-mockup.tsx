import { Brain, CheckCircle2, Flame, XCircle } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

const PURGED = ["CV", "Interview notes", "Transcript", "AI context", "Personal information"];
const RETAINED = ["Skills", "Experience", "Match profile", "Relationship", "Consent state"];

export function TalentMemoryMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/talent-memory" badge="Preview">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-3.5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
            <Flame className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Project Vault</p>
            <p className="text-xs text-muted-foreground">Purged when the search closes</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-border bg-card p-3.5">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Purged
            </p>
            <ul className="mt-2 flex flex-col gap-1.5">
              {PURGED.map((item) => (
                <li key={item} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <XCircle className="h-3.5 w-3.5 shrink-0 text-danger/70" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-brand/20 bg-brand/5 p-3.5">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-brand">
              Talent Memory
            </p>
            <ul className="mt-2 flex flex-col gap-1.5">
              {RETAINED.map((item) => (
                <li key={item} className="flex items-center gap-1.5 text-xs text-foreground">
                  <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <Brain className="h-3.5 w-3.5 shrink-0" />
          Retained only where permitted and configured, per your organisation&apos;s retention
          policy.
        </p>
      </div>
    </BrowserFrame>
  );
}
