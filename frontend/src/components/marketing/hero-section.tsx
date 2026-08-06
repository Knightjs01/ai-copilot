import Image from "next/image";
import Link from "next/link";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

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

          <h1 className="text-4xl font-semibold leading-[1.1] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            The invisible TA partner who never leaves a trace.
          </h1>

          <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
            Phantom appears the moment you open a role, does the heavy lifting of hiring
            alongside you, then disappears the instant you&apos;re done —{" "}
            <span className="font-medium text-foreground">
              taking every candidate record with him
            </span>
            . No names left in your workspace. No CVs left in storage. Nothing left behind.
          </p>

          <p className="text-sm font-medium text-muted-foreground">
            Purpose-built for confidential, high-stakes hiring — where the search itself has to
            stay off the record.
          </p>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring with Phantom</Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <a href="#phantom">Meet Phantom</a>
            </Button>
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
