import Link from "next/link";
import { Briefcase } from "lucide-react";

import { AtsMockup } from "@/components/marketing/mockups/ats-mockup";
import { Button } from "@/components/ui/button";

export function HiringTeamsHeroSection() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-20 lg:grid-cols-2 lg:py-28">
        <div className="flex flex-col items-start gap-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3.5 py-1.5">
            <Briefcase className="h-3.5 w-3.5 text-brand" />
            <span className="text-xs font-semibold uppercase tracking-wide text-brand">
              For hiring teams
            </span>
          </div>

          <h1 className="text-4xl font-semibold leading-[1.1] tracking-tight text-foreground sm:text-5xl">
            Hire privately, screen smart, and leave no trace.
          </h1>

          <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
            Phantom Hire is the ATS built for confidential hiring. Gain access to talent that
            isn&apos;t on the open market, a feature-rich ATS, and &apos;Phantom&apos; — our AI
            partner that helps build hiring blueprints, assists with screening, and burns your
            project once it&apos;s complete.
          </p>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring with Phantom</Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <Link href="/login">Log in</Link>
            </Button>
          </div>
        </div>

        <AtsMockup />
      </div>
    </section>
  );
}
