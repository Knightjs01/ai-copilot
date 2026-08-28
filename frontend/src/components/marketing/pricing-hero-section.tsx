import { Sparkles } from "lucide-react";

export function PricingHeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 px-6 py-16 text-center lg:py-20">
        <div className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3.5 py-1.5">
          <Sparkles className="h-3.5 w-3.5 text-brand" />
          <span className="text-xs font-semibold uppercase tracking-wide text-brand">
            Pricing
          </span>
        </div>

        <h1 className="text-4xl font-semibold leading-[1.1] tracking-tight text-foreground sm:text-5xl">
          Hire beyond the active job market.
        </h1>

        <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
          One platform for anonymous talent discovery, AI-powered hiring, ATS workflows and job
          advertising.
        </p>

        <p className="text-sm font-medium text-foreground">
          Candidates use Phantom for free. Companies pay for the platform.
        </p>
      </div>
    </section>
  );
}
