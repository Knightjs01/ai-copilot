import Image from "next/image";
import Link from "next/link";

import { PassportMockup } from "@/components/marketing/mockups/passport-mockup";
import { Button } from "@/components/ui/button";

export function PassportShowcaseSection() {
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
              The Phantom Passport · Live now
            </p>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            One passport. Every application. Still anonymous.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Build your profile once, skills, experience, achievements, and it travels with you
            to every role you apply for under a Callsign, never your name. Your original CV
            stays encrypted in your Candidate Vault, never shown to recruiters. Every company
            only sees what you&apos;ve reviewed and approved, and your real identity stays
            sealed until you personally approve a Reveal Request.
          </p>
          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/shadow/signup">Build your Passport</Link>
            </Button>
          </div>
        </div>

        <PassportMockup />
      </div>
    </section>
  );
}
