import Image from "next/image";

import { JobBoardMockup } from "@/components/marketing/mockups/job-board-mockup";

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
              Shadow · Live now
            </p>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Meet the people who aren&apos;t applying.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Candidates browse and apply without a profile that outs them to their current
            employer. Companies can list a role without naming themselves until they&apos;re
            ready to. This is the job market you can enter without being seen.
          </p>
        </div>
      </div>
    </section>
  );
}
