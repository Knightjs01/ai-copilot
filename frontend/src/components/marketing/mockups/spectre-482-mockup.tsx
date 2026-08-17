import { EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";
import { CornerMarks } from "@/components/marketing/mockups/corner-marks";

export function Spectre482Mockup() {
  return (
    <div className="relative">
      <CornerMarks />
      <BrowserFrame url="app.phantomhire.com/talent-memory" badge="Preview">
        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-border bg-card p-3.5">
            <p className="text-xs text-muted-foreground">VP Engineering — Fintech</p>
            <p className="mt-1 text-sm font-semibold text-foreground">
              We could already know 14 people.
            </p>
            <p className="text-xs text-muted-foreground">8 from Talent Memory · 6 from Shadow</p>
          </div>

          <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-3.5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand/10 font-mono text-xs font-semibold text-brand">
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
                Matches on skills & experience
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

            <div className="grid grid-cols-3 gap-2 rounded-lg border border-border/60 bg-background/60 p-2.5 text-[11px]">
              <div>
                <p className="text-muted-foreground">Project</p>
                <p className="font-semibold text-foreground">Purged</p>
              </div>
              <div>
                <p className="text-muted-foreground">Talent Memory</p>
                <p className="font-semibold text-foreground">Retained</p>
              </div>
              <div>
                <p className="text-muted-foreground">Identity</p>
                <p className="font-semibold text-foreground">Protected</p>
              </div>
            </div>

            <Button variant="secondary" size="sm" className="mt-1 w-fit">
              Request candidate
            </Button>
          </div>
        </div>
      </BrowserFrame>
    </div>
  );
}
