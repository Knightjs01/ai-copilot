import Image from "next/image";
import Link from "next/link";
import { CheckCircle2, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

const CORE_FEATURES = [
  {
    label: "Phantom Passport",
    detail: "one reusable, anonymous identity that follows candidates everywhere, revealed only when they choose",
  },
  {
    label: "Shadow",
    detail: "the anonymous job board, where candidates search and apply without exposing who they are",
  },
  {
    label: "Phantom ATS",
    detail: "a smart pipeline that ranks candidates by evidence, not names",
  },
  {
    label: "Phantom AI",
    detail: "evidence-based fit assessments across every stage of hiring",
  },
];

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
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col items-start gap-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3.5 py-1.5">
            <Sparkles className="h-3.5 w-3.5 text-brand" />
            <span className="text-xs font-semibold uppercase tracking-wide text-brand">
              Zero-Retention Hiring
            </span>
          </div>

          <h1 className="text-4xl font-semibold leading-[1.05] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            Hiring, without
            <br />
            the exposure.
          </h1>

          <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
            Phantom Hire is the all-in-one platform for anonymous, evidence-based hiring, one
            place to discover, assess, and hire people who aren&apos;t publicly job-searching.
          </p>

          <ul className="flex flex-col gap-2.5">
            {CORE_FEATURES.map((feature) => (
              <li key={feature.label} className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
                <span className="text-base text-foreground/90">
                  <span className="font-semibold text-foreground">{feature.label}</span>
                  {" — "}
                  {feature.detail}
                </span>
              </li>
            ))}
          </ul>

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
          <div className="absolute h-80 w-80 rounded-full bg-brand/20 blur-3xl" aria-hidden />
          <div className="absolute h-56 w-56 rounded-full bg-electric/10 blur-3xl" aria-hidden />
          <Image
            src="/phantom-ghost-hero.png"
            alt="Phantom, the invisible TA partner"
            width={668}
            height={844}
            className="relative h-72 w-auto animate-float drop-shadow-2xl sm:h-96"
            priority
          />
        </div>
      </div>
    </section>
  );
}
