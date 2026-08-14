import { EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

export function Spectre482Mockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/talent-memory" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="rounded-xl border border-border bg-white p-3.5">
          <p className="text-xs text-muted-foreground">VP Engineering — Fintech</p>
          <p className="mt-1 text-sm font-semibold text-foreground">
            We already know 14 people.
          </p>
          <p className="text-xs text-muted-foreground">8 from Talent Memory · 6 from Shadow</p>
        </div>

        <div className="flex flex-col gap-3 rounded-xl border border-border bg-white p-3.5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand/10 text-xs font-semibold text-brand">
              S-482
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Spectre-482</p>
              <p className="flex items-center gap-1 text-[11px] text-muted-foreground">
                <EyeOff className="h-3 w-3 shrink-0" />
                Senior Product / Engineering Leader
              </p>
            </div>
            <span className="ml-auto shrink-0 rounded-full bg-success/10 px-2.5 py-1 text-[11px] font-semibold text-success">
              96% match
            </span>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {["Fintech", "Payments", "SaaS", "UK"].map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-border bg-secondary/40 px-2 py-0.5 text-[10px] font-medium text-foreground"
              >
                {tag}
              </span>
            ))}
          </div>

          <div className="flex items-center justify-between text-[11px] text-muted-foreground">
            <span>
              Project: <span className="font-semibold text-foreground">Purged</span>
            </span>
            <span>
              Talent Memory: <span className="font-semibold text-foreground">Retained</span>
            </span>
            <span>
              Identity: <span className="font-semibold text-foreground">Protected</span>
            </span>
          </div>

          <Button variant="secondary" size="sm" className="mt-1 w-fit">
            Request candidate
          </Button>
        </div>
      </div>
    </BrowserFrame>
  );
}
