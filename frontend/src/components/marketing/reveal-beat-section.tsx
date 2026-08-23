import Image from "next/image";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { RevealIdentityMockup } from "@/components/marketing/mockups/reveal-identity-mockup";
import { Button } from "@/components/ui/button";

// A homepage-scoped copy of the "Identity Vault" beat, distinct from
// reveal-identity-showcase-section.tsx (used on /hiring-teams) -- same real,
// already-"Live now" mockup, its own copy, so later /hiring-teams changes don't ripple here.
const KEY_POINTS = [
  "Every candidate stays a Callsign until an Owner reveals them",
  "Reveal requires a stated reason and a fresh step-up check",
  "Every reveal is recorded in the audit trail, permanently",
];

export function RevealBeatSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-2">
            <Image src="/phantom-icon.png" alt="" width={234} height={190} className="h-4 w-auto" />
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              Identity Vault · Live now
            </p>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Anonymous until you choose otherwise.
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
            <Button asChild variant="secondary" size="lg">
              <Link href="/hiring-teams">See how reveal works</Link>
            </Button>
          </div>
        </div>

        <RevealIdentityMockup />
      </div>
    </section>
  );
}
