import Image from "next/image";
import Link from "next/link";
import { EyeOff, LayoutGrid, Search, Sparkles, type LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

const CORE_FEATURES: { Icon: LucideIcon; label: string; detail: string }[] = [
  { Icon: EyeOff, label: "Phantom Passport", detail: "Anonymous, reusable candidate identity" },
  { Icon: Search, label: "Shadow", detail: "Anonymous job board for hidden talent" },
  { Icon: LayoutGrid, label: "Phantom ATS", detail: "Smart pipeline ranked by evidence" },
  { Icon: Sparkles, label: "Phantom AI", detail: "Evidence-based fit assessments" },
];

const SPECIALIST_SECTORS = [
  "Technology",
  "Security & Intelligence",
  "Financial Services",
  "Defence",
  "Aerospace & Executive Search",
];

function FeatureCard({ Icon, label, detail }: { Icon: LucideIcon; label: string; detail: string }) {
  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-3.5 shadow-sm shadow-slate-900/[0.04]">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand/10 text-brand">
        <Icon className="h-4 w-4" />
      </div>
      <p className="text-sm font-semibold leading-tight text-foreground">{label}</p>
      <p className="text-xs leading-snug text-muted-foreground">{detail}</p>
    </div>
  );
}

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

        <div className="flex flex-col items-center gap-5">
          <div className="grid w-full max-w-xs grid-cols-2 gap-3 sm:max-w-sm">
            {CORE_FEATURES.slice(0, 2).map((feature) => (
              <FeatureCard key={feature.label} {...feature} />
            ))}
          </div>

          <div className="relative flex items-center justify-center">
            <div className="absolute h-56 w-56 rounded-full bg-brand/20 blur-3xl" aria-hidden />
            <div className="absolute h-40 w-40 rounded-full bg-electric/10 blur-3xl" aria-hidden />
            <Image
              src="/phantom-ghost-hero.png"
              alt="Phantom, the invisible TA partner"
              width={668}
              height={844}
              className="relative h-44 w-auto animate-float drop-shadow-2xl sm:h-52"
              priority
            />
          </div>

          <div className="grid w-full max-w-xs grid-cols-2 gap-3 sm:max-w-sm">
            {CORE_FEATURES.slice(2, 4).map((feature) => (
              <FeatureCard key={feature.label} {...feature} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
