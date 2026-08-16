import Link from "next/link";

import { PassportDetailMockup } from "@/components/marketing/mockups/passport-detail-mockup";
import { Button } from "@/components/ui/button";

export function PassportHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Candidate Passport
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Apply everywhere. Reveal nothing until you choose to.
          </h1>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Build your professional record once — skills, experience, achievements — and it
            travels with you to every role you apply for under a Callsign, never your name. You
            review and approve exactly what goes live, and your real identity stays sealed until
            you personally approve a Reveal Request.
          </p>
          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/shadow/signup">Build your Passport</Link>
            </Button>
          </div>
        </div>

        <PassportDetailMockup />
      </div>
    </section>
  );
}
