import Image from "next/image";
import Link from "next/link";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

const PROMISE_ITEMS = [
  "Anonymous by default",
  "AI-matched",
  "Verified when it matters",
  "Zero-retention when the project is done",
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
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-20 lg:grid-cols-2 lg:py-28">
        <div className="flex flex-col items-start gap-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3.5 py-1.5">
            <Sparkles className="h-3.5 w-3.5 text-brand" />
            <span className="text-xs font-semibold uppercase tracking-wide text-brand">
              The world&apos;s first Zero-Retention Hiring Platform
            </span>
          </div>

          <h1 className="text-3xl font-semibold leading-[1.1] tracking-tight text-foreground sm:text-4xl lg:text-5xl">
            Zero-Retention
            <br />
            Anonymous Hiring
          </h1>

          <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
            Phantom Hire is the private talent marketplace where exceptional people can explore
            their next opportunity without revealing their identity — and companies can
            discover them with total anonymity.
          </p>

          <ul className="flex flex-wrap gap-2">
            {PROMISE_ITEMS.map((item) => (
              <li
                key={item}
                className="rounded-full border border-border bg-white px-3.5 py-1.5 text-xs font-medium text-foreground"
              >
                {item}
              </li>
            ))}
          </ul>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring with Phantom</Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <a href="#phantom">Meet Phantom</a>
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
          <div className="absolute h-72 w-72 rounded-full bg-brand/10 blur-3xl" aria-hidden />
          <Image
            src="/phantom-icon.png"
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
