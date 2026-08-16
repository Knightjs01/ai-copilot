import { CheckCircle2, Flame, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";

const REAL_TODAY = [
  "Every CV, interview note, and transcript lives inside a project's own Project Vault.",
  "When a project closes, its Vault can be purged entirely — a real, cascading deletion.",
  "A Purge Certificate records exactly what data categories were destroyed, and when.",
];

const BUILDING_NEXT = [
  "A permitted, consent-respecting layer that keeps a candidate's skills and match profile.",
  "No identity, no CV, no interview notes carried forward — only what's needed to rediscover fit.",
  "Configurable per organisation, and only where retention is permitted.",
];

export function TalentMemoryRoadmapSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            What&apos;s real, what&apos;s next
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            The destruction is real today. The memory is what we&apos;re building.
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]">
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <Flame className="h-4 w-4" />
              </div>
              <p className="text-sm font-semibold text-foreground">Real today</p>
            </div>
            <ul className="flex flex-col gap-2.5">
              {REAL_TODAY.map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                  <span className="text-foreground/80">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col gap-4 rounded-2xl border border-brand/20 bg-brand/5 p-6">
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <Sparkles className="h-4 w-4" />
              </div>
              <p className="text-sm font-semibold text-foreground">What we&apos;re building</p>
              <Badge variant="outline">Preview</Badge>
            </div>
            <ul className="flex flex-col gap-2.5">
              {BUILDING_NEXT.map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm">
                  <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                  <span className="text-foreground/80">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
