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
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col items-start gap-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3.5 py-1.5">
            <Sparkles className="h-3.5 w-3.5 text-brand" />
            <span className="text-xs font-semibold uppercase tracking-wide text-brand">
              Zero-Retention Hiring
            </span>
          </div>

          <h1 className="text-4xl font-semibold leading-[1.05] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            Hire with
            <br />
            total anonymity
          </h1>

          <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
            Phantom Hire is the all-in-one platform for anonymous, evidence-based hiring, one
            place to discover, assess, and hire people who aren&apos;t publicly job-searching.
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
          <Image
            src="/phantom-hero-image.png"
            alt="Phantom Passport, Shadow, Phantom ATS, and Phantom AI working together around the Phantom ghost"
            width={1536}
            height={1024}
            className="relative w-full max-w-xl animate-float"
            priority
          />
        </div>
      </div>
    </section>
  );
}
