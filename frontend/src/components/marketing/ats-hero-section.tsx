import Image from "next/image";
import Link from "next/link";
import {
  BarChart3,
  EyeOff,
  MessageSquareText,
  Sparkles,
  Star,
  Target,
  ShieldCheck,
  Workflow,
} from "lucide-react";

import { AtsAppShellMockup } from "@/components/marketing/mockups/ats-app-shell-mockup";
import { Button } from "@/components/ui/button";

const FEATURES = [
  {
    icon: Workflow,
    title: "Hiring projects",
    body: "One real pipeline per role, whether candidates came from Shadow or were added directly.",
  },
  {
    icon: Target,
    title: "Smart role calibration",
    body: "Turn a role brief into structured must-haves, nice-to-haves, and evaluation criteria before you screen a single candidate.",
  },
  {
    icon: Sparkles,
    title: "Phantom AI Screening Assistant",
    body: "Generate an evidence-based fit assessment on demand: strengths, gaps, and exactly what to ask next.",
  },
  {
    icon: MessageSquareText,
    title: "Interview prep & handoff notes",
    body: "Walk into the call with the right questions, then turn your own notes into a clean handoff summary afterward.",
  },
  {
    icon: ShieldCheck,
    title: "AI fit rating",
    body: "Every candidate rated Strong, Good, Possible, or Weak Fit, with the evidence attached.",
  },
  {
    icon: EyeOff,
    title: "Anonymous candidate profiles",
    body: "Every candidate shows up as a Callsign, not a name, until you're ready to know who they are.",
  },
  {
    icon: Star,
    title: "Hiring priority tracking",
    body: "Hiring managers submit their top priorities once, see exactly which candidates meet them, backed by evidence.",
  },
  {
    icon: BarChart3,
    title: "Pipeline analytics",
    body: "Live breakdowns by stage, fit rating, source, and outcome, know where your pipeline actually stands.",
  },
];

export function AtsHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <div className="flex items-center gap-2">
            <Image
              src="/phantom-icon.png"
              alt=""
              width={234}
              height={190}
              className="h-4 w-auto"
            />
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              Phantom ATS
            </p>
          </div>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Every candidate ranked by evidence.
          </h1>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Hiring projects, Callsigns instead of names, AI fit ratings, and a live dashboard of
            exactly what needs your attention next. Dense, organised, and built for the team
            that lives inside it every day.
          </p>
          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring with Phantom</Link>
            </Button>
          </div>
        </div>

        <AtsAppShellMockup />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="flex flex-col gap-2.5 rounded-2xl border border-border bg-card p-5 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <feature.icon className="h-4 w-4" />
              </div>
              <p className="text-sm font-semibold text-foreground">{feature.title}</p>
              <p className="text-sm leading-relaxed text-muted-foreground">{feature.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
