import Image from "next/image";
import Link from "next/link";

import { AtsDashboardMockup } from "@/components/marketing/mockups/ats-dashboard-mockup";
import { Button } from "@/components/ui/button";

export function AtsHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <div className="flex items-center gap-2">
            <Image src="/phantom-icon.png" alt="" width={234} height={190} className="h-4 w-auto" />
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">Phantom ATS</p>
          </div>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Your ATS. With a brain.
          </h1>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Hiring projects, Callsigns instead of names, AI fit ratings, and a live dashboard of
            exactly what needs your attention next. Dense, organised, and built for the team that
            lives inside it every day.
          </p>
          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring with Phantom</Link>
            </Button>
          </div>
        </div>

        <AtsDashboardMockup />
      </div>
    </section>
  );
}
