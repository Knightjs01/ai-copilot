import Image from "next/image";

import { JobApplicationMockup } from "@/components/marketing/mockups/job-application-mockup";

export function JobApplicationShowcaseSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-2">
            <Image
              src="/shadow-icon.png"
              alt=""
              width={557}
              height={550}
              className="h-4 w-auto"
            />
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              Applying, anonymously
            </p>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            One click to apply, no name attached
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            You&apos;re issued a Callsign the moment you apply. Your CV is automatically
            redacted before it reaches anyone on the other side, so the first thing a hiring
            team sees is your experience, not your name, current employer, or contact details.
          </p>
        </div>

        <JobApplicationMockup />
      </div>
    </section>
  );
}
