import Image from "next/image";
import Link from "next/link";
import { ArrowRight, CheckCircle2, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { AiSparkIcon } from "@/components/marketing/icons/ai-spark-icon";
import { AtsGridIcon } from "@/components/marketing/icons/ats-grid-icon";
import { ShadowMaskIcon } from "@/components/marketing/icons/shadow-mask-icon";
import { PhantomHeroCompositeMockup } from "@/components/marketing/mockups/phantom-hero-composite-mockup";

const FEATURE_ROW = [
  { Icon: ShadowMaskIcon, name: "Shadow", tagline: "Anonymous Job Board" },
  { Icon: AtsGridIcon, name: "Phantom ATS", tagline: "End-to-end Hiring" },
  { Icon: AiSparkIcon, name: "Phantom AI", tagline: "Evidence-based Co-pilot" },
];

const TRUST_ITEMS = [
  "Anonymous by default",
  "Candidate-controlled identity",
  "Privacy-first architecture",
];

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col items-start gap-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3.5 py-1.5">
            <Sparkles className="h-3.5 w-3.5 text-brand" />
            <span className="text-xs font-semibold uppercase tracking-wide text-brand">
              The Private Hiring Platform
            </span>
          </div>

          <h1 className="text-4xl font-semibold leading-[1.05] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            Hire exceptional
            <br />
            people.
            <br />
            <span className="text-brand">Without the exposure.</span>
          </h1>

          <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
            An all-in-one hiring platform combining an anonymous job board, a feature-rich ATS,
            and a Phantom AI co-pilot, helping recruiters discover, assess and hire exceptional
            talent while candidates stay in control of their identity.
          </p>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {FEATURE_ROW.map((feature) => (
              <div key={feature.name} className="flex items-center gap-2.5">
                <feature.Icon />
                <div>
                  <p className="text-sm font-semibold text-foreground">{feature.name}</p>
                  <p className="text-xs text-muted-foreground">{feature.tagline}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button asChild variant="brand" size="lg">
              <Link href="/signup" className="inline-flex items-center gap-2">
                Start hiring
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <Link href="/shadow-job-board" className="inline-flex items-center gap-2">
                Explore Shadow
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>

          <ul className="flex flex-wrap gap-x-5 gap-y-2">
            {TRUST_ITEMS.map((item) => (
              <li key={item} className="flex items-center gap-1.5 text-sm text-foreground">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-brand" />
                {item}
              </li>
            ))}
          </ul>

          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-foreground underline-offset-4 hover:underline">
              Log in
            </Link>
          </p>
        </div>

        <PhantomHeroCompositeMockup />

        <div className="relative flex items-center justify-center lg:hidden">
          <div className="absolute h-72 w-72 rounded-full bg-brand/20 blur-3xl" aria-hidden />
          <Image
            src="/phantom-ghost-hero.png"
            alt="Phantom, the invisible TA partner"
            width={668}
            height={844}
            className="relative h-64 w-auto animate-float drop-shadow-2xl"
            priority
          />
        </div>
      </div>
    </section>
  );
}
