import { EyeOff } from "lucide-react";

import { CandidatePortalMockup } from "@/components/marketing/mockups/candidate-portal-mockup";

export function JobSeekersHeroSection() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-20 lg:grid-cols-2 lg:py-28">
        <div className="flex flex-col items-start gap-6">
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
            Stay a &apos;Callsign&apos; on Shadow, our Anonymous Job Board. Explore roles, get
            AI-matched to opportunities, and keep your identity private until you choose to
            reveal it.
          </p>

          <span className="rounded-full border border-border bg-white px-3.5 py-1.5 text-xs font-medium text-muted-foreground">
            In development — here&apos;s what it looks like
          </span>
        </div>

        <CandidatePortalMockup />
      </div>
    </section>
  );
}
