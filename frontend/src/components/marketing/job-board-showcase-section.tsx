import Image from "next/image";
import { CheckCircle2 } from "lucide-react";

import { JobBoardMockup } from "@/components/marketing/mockups/job-board-mockup";

const KEY_POINTS = [
  "Browse and apply without alerting your current employer",
  "See salary and role details upfront, no guessing",
  "Apply once with your Phantom Passport, use it everywhere",
  "Reveal who you are only when you choose to",
];

export function JobBoardShowcaseSection() {
  return (
    <section id="shadow-beat" className="border-t border-border bg-secondary/20">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="order-2 lg:order-1">
          <JobBoardMockup />
        </div>

        <div className="order-1 flex flex-col gap-5 lg:order-2">
          <div className="flex items-center gap-2">
            <Image
              src="/shadow-icon.png"
              alt=""
              width={557}
              height={550}
              className="h-4 w-auto"
            />
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              Shadow - Anonymous Talent Network · Live now
            </p>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            The next generation hiring marketplace, for candidates who value anonymity.
          </h2>
          <ul className="flex flex-col gap-2.5">
            {KEY_POINTS.map((point) => (
              <li key={point} className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
                <span className="text-base text-foreground/90">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
