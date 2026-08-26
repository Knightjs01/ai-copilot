import Image from "next/image";
import Link from "next/link";
import { EyeOff, ShieldCheck, Sparkles, UserRound } from "lucide-react";

import { CandidatePortalMockup } from "@/components/marketing/mockups/candidate-portal-mockup";
import { Button } from "@/components/ui/button";

const OVERVIEW_STEPS = [
  {
    icon: UserRound,
    title: "Build a Passport",
    body: "One reusable profile with your real skills and experience, built once and used everywhere you apply.",
  },
  {
    icon: Sparkles,
    title: "Get matched, anonymously",
    body: "Browse and apply to roles on Shadow under a Callsign, not your name, your photo, or your employer history.",
  },
  {
    icon: ShieldCheck,
    title: "Reveal on your terms",
    body: "A company only learns who you are once you approve their reveal request. Until then, you're a Callsign.",
  },
];

export function JobSeekersHeroSection() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
          <div className="flex flex-col items-start gap-6">
            <Image
              src="/phantom-shadow-logo-new.png"
              alt="Phantom Shadow: Anonymous Job Board"
              width={2172}
              height={724}
              className="h-9 w-auto"
              priority
            />

            <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3.5 py-1.5">
              <EyeOff className="h-3.5 w-3.5 text-brand" />
              <span className="text-xs font-semibold uppercase tracking-wide text-brand">
                For job seekers
              </span>
            </div>

            <h1 className="text-4xl font-semibold leading-[1.1] tracking-tight text-foreground sm:text-5xl">
              Look for your next role, with total anonymity.
            </h1>

            <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
              Shadow is Phantom Hire&apos;s anonymous job board. Build a Phantom Passport once,
              apply to roles as a Callsign, and stay invisible to your current employer, your
              network, and every company you haven&apos;t chosen to reveal yourself to.
            </p>

            <div className="flex flex-col gap-3 sm:flex-row">
              <Button asChild variant="brand" size="lg">
                <Link href="/shadow/signup">Build your Phantom Passport</Link>
              </Button>
              <Button asChild variant="secondary" size="lg">
                <Link href="/shadow/login">Log in</Link>
              </Button>
            </div>
          </div>

          <CandidatePortalMockup />
        </div>

        <div className="mt-16 grid grid-cols-1 gap-8 border-t border-border pt-10 sm:grid-cols-3">
          {OVERVIEW_STEPS.map((step, i) => (
            <div key={step.title} className="flex flex-col gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Step {i + 1}
              </span>
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand/10 text-brand">
                  <step.icon className="h-4 w-4" />
                </div>
                <h3 className="text-base font-semibold text-foreground">{step.title}</h3>
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground">{step.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
