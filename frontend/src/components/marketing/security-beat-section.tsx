import Link from "next/link";
import { CheckCircle2, ChevronRight, Lock, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";

const FLOW_STEPS = ["Candidate", "Passport", "Shadow", "Callsign", "Phantom ATS", "Recruiter"];

const KEY_POINTS = [
  "Real identity never travels with a candidate's profile",
  "Sealed behind mandatory MFA and a step-up re-check",
  "Only unseals when a candidate approves a Reveal Request",
];

export function SecurityBeatSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-10 px-6 py-16 text-center lg:py-20">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-brand" />
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Security · Private by architecture
          </p>
        </div>
        <h2 className="max-w-2xl text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Identity stays protected until the candidate chooses otherwise.
        </h2>
        <ul className="mx-auto flex flex-col items-start gap-2.5 text-left">
          {KEY_POINTS.map((point) => (
            <li key={point} className="flex items-start gap-2.5">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
              <span className="text-base text-foreground/90">{point}</span>
            </li>
          ))}
        </ul>

        <div className="flex flex-wrap items-center justify-center gap-2">
          {FLOW_STEPS.map((step, index) => (
            <div key={step} className="flex items-center gap-2">
              <span className="rounded-full border border-border bg-card px-3.5 py-1.5 text-xs font-medium text-foreground">
                {step}
              </span>
              {index < FLOW_STEPS.length - 1 && (
                <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden />
              )}
            </div>
          ))}
        </div>
        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Lock className="h-3.5 w-3.5" />
          Identity locked at every step until a Reveal Request is approved
        </p>

        <Button asChild variant="secondary" size="lg">
          <Link href="/trust">See what&apos;s actually implemented</Link>
        </Button>
      </div>
    </section>
  );
}
