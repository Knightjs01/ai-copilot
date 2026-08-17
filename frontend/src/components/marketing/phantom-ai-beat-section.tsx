import Image from "next/image";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { AiAssessmentMockup } from "@/components/marketing/mockups/ai-assessment-mockup";
import { Button } from "@/components/ui/button";

const KEY_POINTS = [
  "Evidence-based fit assessment for any candidate",
  "Strengths, gaps, and exactly which question to ask next",
  "Works from the role brief and the candidate's own record, never a black-box score",
];

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
            Phantom AI beside every recruiter.
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
              <Link href="/signup">Start hiring</Link>
            </Button>
          </div>
        </div>

        <AiAssessmentMockup />
      </div>
    </section>
  );
}
