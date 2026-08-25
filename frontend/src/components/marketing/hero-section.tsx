import Image from "next/image";
import Link from "next/link";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

const SPECIALIST_SECTORS = [
  "Technology",
  "Security & Intelligence",
  "Financial Services",
  "Defence",
  "Aerospace & Executive Search",
];

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      {/* Subtle Ghost watermark -- a brand signature, not a hero illustration. Placed first so it
          sits behind every other element without an explicit z-index, per the brand guideline
          that the Ghost is a discreet signature, never something competing with the Passport. */}
      <Image
        src="/phantom-icon.png"
        alt=""
        width={650}
        height={826}
        aria-hidden
        className="pointer-events-none absolute -bottom-24 -right-24 h-[420px] w-auto select-none opacity-[0.04]"
      />

      <div className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col items-start gap-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3.5 py-1.5">
            <Sparkles className="h-3.5 w-3.5 text-brand" />
            <span className="text-xs font-semibold uppercase tracking-wide text-brand">
              Zero-Retention Hiring
            </span>
          </div>

          <h1 className="text-4xl font-semibold leading-[1.05] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            The Private Talent Marketplace
          </h1>

          <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
            Phantom Hire is the all-in-one platform for anonymous, evidence-based hiring, built
            around the Candidate Passport: one reusable, verifiable, anonymous profile for people
            who aren&apos;t publicly job-searching.
          </p>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring</Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <a href="#shadow-beat">See how it works</a>
            </Button>
          </div>

          <div className="flex flex-col gap-2.5">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Built for specialist sectors
            </p>
            <div className="flex flex-wrap gap-2">
              {SPECIALIST_SECTORS.map((sector) => (
                <span
                  key={sector}
                  className="rounded-full border border-brand/20 bg-brand/5 px-3 py-1 text-xs font-medium text-foreground"
                >
                  {sector}
                </span>
              ))}
            </div>
          </div>

          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-foreground underline-offset-4 hover:underline">
              Log in
            </Link>
          </p>
        </div>

        <div className="relative flex items-center justify-center">
          <div className="shrink-0 lg:translate-x-6">
            <div className="animate-float w-full max-w-xl lg:w-[620px] lg:max-w-none">
              <Image
                src="/phantom-hire-hero-composite.png"
                alt="Phantom Hire's Ghost, Phantom ATS pipeline and the Phantom mobile app showing anonymous candidate matches"
                width={1536}
                height={1024}
                sizes="(max-width: 1024px) 90vw, 620px"
                quality={95}
                priority
                className="h-auto w-full"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
