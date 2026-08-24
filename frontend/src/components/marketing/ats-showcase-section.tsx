import Image from "next/image";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { AtsAppShellMockup } from "@/components/marketing/mockups/ats-app-shell-mockup";
import { Button } from "@/components/ui/button";

const KEY_POINTS = [
  "Hiring projects with Callsigns instead of names",
  "Smart role calibration from your role brief",
  "AI fit ratings on every candidate, backed by evidence",
  "AI screening assistant: strengths, gaps, and what to ask next",
  "Hiring priority tracking against real hiring-manager requirements",
  "Live pipeline analytics by stage, fit rating, and source",
  "A live dashboard of exactly what needs your attention next",
];

export function AtsShowcaseSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-2">
            <Image
              src="/phantom-icon.png"
              alt=""
              width={234}
              height={190}
              className="h-4 w-auto"
            />
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              The Phantom Talent ATS · Live now
            </p>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Candidate profile comes first, the identity comes later.
          </h2>
          <ul className="flex flex-col gap-2.5">
            {KEY_POINTS.map((point) => (
              <li key={point} className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
                <span className="text-base text-foreground/90">{point}</span>
              </li>
            ))}
          </ul>
          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring with Phantom</Link>
            </Button>
          </div>
        </div>

        <div className="relative max-h-[420px] overflow-hidden rounded-2xl">
          <AtsAppShellMockup />
          <div
            className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-background to-transparent"
            aria-hidden
          />
        </div>
      </div>
    </section>
  );
}
