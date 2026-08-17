import Image from "next/image";
import { Brain, CheckCircle2, Lock, MoreHorizontal, Plus, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";

// Dense, multi-panel hero visual — deliberately not wrapped in the shared BrowserFrame (every
// other mockup on the site is a fake screenshot; this is a free-floating illustrated
// composition, matching the flagship hero treatment). Every data shape is real (FitRating,
// real pipeline stages, real Hiring Manager Alignment top_requirements, real Talent Memory
// Preview status, real Zero-Retention purge) — illustrative sample values only, same
// convention as every other mockup on this site. No numeric match scores, no "AI listens live"
// claim — both were in the reference design but don't match the real product.

const TOP_CANDIDATES = [
  { callsign: "Spectre-482", tags: ["Fintech", "Payments"], stage: "Interviewing", fit: "Strong Fit" as const },
  { callsign: "Wraith-731", tags: ["Fintech", "Infra"], stage: "Screening", fit: "Good Fit" as const },
  { callsign: "Ghost-214", tags: ["Engineering"], stage: "Interviewing", fit: "Possible Fit" as const },
];

const FIT_VARIANT = {
  "Strong Fit": "success",
  "Good Fit": "info",
  "Possible Fit": "warning",
} as const;

const PIPELINE = [
  { label: "New", value: 37 },
  { label: "Screening", value: 22 },
  { label: "Interviewing", value: 5 },
  { label: "Offer", value: 2 },
];

const REQUIREMENTS = ["Payments experience", "Technical leadership", "Enterprise scale"];

export function PhantomHeroCompositeMockup() {
  return (
    <div className="relative mx-auto hidden w-full max-w-lg lg:block">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="flex w-40 flex-col gap-2.5 rounded-2xl border border-border bg-card p-3 shadow-xl shadow-slate-900/[0.08]">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Shadow
          </p>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand/10 font-mono text-[10px] font-semibold text-brand">
              S-482
            </div>
            <Badge variant="success" className="text-[10px]">
              Strong Fit
            </Badge>
          </div>
          <div className="flex flex-wrap gap-1">
            {["Fintech", "Payments", "SaaS"].map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-border bg-secondary/40 px-1.5 py-0.5 text-[9px] text-foreground/80"
              >
                {tag}
              </span>
            ))}
          </div>
          <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
            <Lock className="h-2.5 w-2.5 shrink-0" />
            Identity protected
          </p>
        </div>

        <div className="relative mt-2 h-24 w-24 shrink-0">
          <div className="absolute inset-0 rounded-full bg-brand/25 blur-2xl" aria-hidden />
          <Image
            src="/phantom-ghost-hero.png"
            alt="Phantom, the invisible TA partner"
            width={300}
            height={300}
            className="relative h-full w-full object-contain drop-shadow-xl"
            priority
          />
        </div>

        <div className="flex w-32 flex-col items-end gap-3 pt-2 text-right">
          <div>
            <p className="text-xs font-semibold text-brand">Phantom AI</p>
            <p className="mt-0.5 text-[10px] leading-snug text-muted-foreground">
              Shows its evidence, never just a score.
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-brand">Phantom ATS</p>
            <p className="mt-0.5 text-[10px] leading-snug text-muted-foreground">
              One operating system for the whole hire.
            </p>
          </div>
        </div>
      </div>

      <div className="relative rounded-2xl border border-border bg-card p-4 shadow-2xl shadow-slate-900/[0.12]">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-foreground">VP Engineering</p>
              <Badge variant="success" className="text-[10px]">
                Open
              </Badge>
            </div>
            <p className="text-[11px] text-muted-foreground">London, UK · Full-time</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-lg bg-brand px-2.5 py-1.5 text-[11px] font-medium text-brand-foreground">
              <Plus className="mr-1 inline h-3 w-3" />
              Add candidate
            </span>
            <MoreHorizontal className="h-4 w-4 shrink-0 text-muted-foreground" />
          </div>
        </div>

        <div className="mt-3 flex items-center gap-4 border-b border-border pb-2 text-[11px] text-muted-foreground">
          {["Overview", "Pipeline", "Candidates", "AI insights", "Analytics"].map((tab, i) => (
            <span key={tab} className={i === 1 ? "font-medium text-foreground" : undefined}>
              {tab}
            </span>
          ))}
        </div>

        <div className="mt-3 grid grid-cols-4 gap-2">
          {PIPELINE.map((stage) => (
            <div key={stage.label} className="rounded-lg border border-border/60 bg-background/60 px-2 py-1.5">
              <p className="text-[10px] text-muted-foreground">{stage.label}</p>
              <p className="font-mono text-sm font-semibold tabular-nums text-foreground">{stage.value}</p>
            </div>
          ))}
        </div>

        <div className="mt-3 flex flex-col gap-2">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Top candidates
          </p>
          {TOP_CANDIDATES.map((candidate) => (
            <div
              key={candidate.callsign}
              className="flex items-center justify-between gap-2 rounded-lg border border-border/60 bg-background/60 px-2.5 py-2"
            >
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand/10 font-mono text-[9px] font-semibold text-brand">
                  {candidate.callsign.slice(0, 2)}
                </div>
                <div>
                  <p className="text-xs font-medium text-foreground">{candidate.callsign}</p>
                  <div className="flex gap-1">
                    {candidate.tags.map((tag) => (
                      <span key={tag} className="text-[9px] text-muted-foreground">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-1.5">
                <span className="text-[10px] text-muted-foreground">{candidate.stage}</span>
                <Badge variant={FIT_VARIANT[candidate.fit]} className="text-[9px]">
                  {candidate.fit}
                </Badge>
              </div>
            </div>
          ))}
        </div>

        <div className="absolute -right-5 -top-7 w-48 rounded-2xl border border-border bg-card p-3 shadow-xl shadow-slate-900/[0.1]">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-brand">
            Hiring manager alignment
          </p>
          <p className="mt-1 text-[11px] leading-snug text-foreground">
            3 candidates meet every priority.
          </p>
          <ul className="mt-2 flex flex-col gap-1">
            {REQUIREMENTS.map((req) => (
              <li key={req} className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                <CheckCircle2 className="h-3 w-3 shrink-0 text-success" />
                {req}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="flex items-start gap-2 rounded-xl border border-border bg-card p-3 shadow-lg shadow-slate-900/[0.06]">
          <Brain className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
          <div>
            <p className="flex items-center gap-1.5 text-[11px] font-semibold text-foreground">
              Talent Memory
              <span className="rounded-full border border-border px-1.5 py-0.5 text-[8px] font-medium uppercase text-muted-foreground">
                Preview
              </span>
            </p>
            <p className="mt-0.5 text-[10px] leading-snug text-muted-foreground">
              Rediscover great talent from past projects.
            </p>
          </div>
        </div>
        <div className="flex items-start gap-2 rounded-xl border border-border bg-card p-3 shadow-lg shadow-slate-900/[0.06]">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
          <div>
            <p className="text-[11px] font-semibold text-foreground">Zero-Retention</p>
            <p className="mt-0.5 text-[10px] leading-snug text-muted-foreground">
              Keep what matters. Purge what you don&apos;t.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
