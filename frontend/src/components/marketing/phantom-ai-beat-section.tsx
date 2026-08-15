import Image from "next/image";
import Link from "next/link";

import { AiAssessmentMockup } from "@/components/marketing/mockups/ai-assessment-mockup";
import { Button } from "@/components/ui/button";

export function PhantomAiBeatSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-2">
            <Image src="/phantom-icon.png" alt="" width={234} height={190} className="h-4 w-auto" />
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              Phantom AI · Live now
            </p>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            AI beside every recruiter.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Generate an evidence-based fit assessment for any candidate: what&apos;s strong, what
            still needs probing, and exactly which question to ask next. Phantom AI works from the
            role brief and the candidate&apos;s own record, not a black-box score.
          </p>
          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring</Link>
            </Button>
          </div>
        </div>

        <AiAssessmentMockup />
      </div>
    </section>
  );
}
