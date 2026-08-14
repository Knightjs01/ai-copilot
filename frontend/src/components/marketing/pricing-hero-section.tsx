import Link from "next/link";
import { ArrowRight, Brain, Briefcase, EyeOff, Flame, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

const FLOW_STEPS = [
  { icon: EyeOff, label: "Shadow" },
  { icon: Briefcase, label: "Phantom ATS" },
  { icon: Sparkles, label: "Phantom AI" },
  { icon: Brain, label: "Talent Memory" },
  { icon: Flame, label: "Project Purge" },
];

export function PricingHeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-6 py-16 text-center lg:py-20">
        <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3.5 py-1.5">
          <Sparkles className="h-3.5 w-3.5 text-brand" />
          <span className="text-xs font-semibold uppercase tracking-wide text-brand">
            Pricing & commercial model
          </span>
        </div>

        <h1 className="text-3xl font-semibold leading-[1.1] tracking-tight text-foreground sm:text-4xl lg:text-5xl">
          Hiring should be private.
          <br />
          Your talent network should be permanent.
        </h1>

        <p className="max-w-2xl text-lg leading-relaxed text-muted-foreground">
          Phantom gives companies the infrastructure to discover, assess and hire exceptional
          people, without treating candidate data like something you need to keep forever.
          Candidates are free. Companies pay for the infrastructure, intelligence and security
          that make Phantom different.
        </p>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Button asChild variant="brand" size="lg">
            <Link href="/signup">Start Hiring Free</Link>
          </Button>
          <Button asChild variant="secondary" size="lg">
            <Link href="/shadow/signup">Create Your Phantom Passport</Link>
          </Button>
        </div>
      </div>

      <div className="relative mx-auto max-w-4xl px-6 pb-16 lg:pb-20">
        <div className="absolute inset-x-0 top-1/2 h-40 -translate-y-1/2 rounded-full bg-brand/10 blur-3xl" aria-hidden />
        <div className="relative flex flex-wrap items-center justify-center gap-3 rounded-2xl border border-border bg-white p-6 shadow-sm shadow-slate-900/[0.03] sm:gap-4 sm:p-8">
          {FLOW_STEPS.map((step, i) => (
            <div key={step.label} className="flex items-center gap-3 sm:gap-4">
              <div className="flex flex-col items-center gap-2">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand/10 text-brand">
                  <step.icon className="h-5 w-5" />
                </div>
                <span className="text-xs font-medium text-muted-foreground">{step.label}</span>
              </div>
              {i < FLOW_STEPS.length - 1 && (
                <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground/50" aria-hidden />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
