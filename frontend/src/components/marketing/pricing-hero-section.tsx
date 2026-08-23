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
          Simple pricing for a smarter way to hire.
        </h1>

        <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
          Start with the hiring platform. Add private talent discovery and intelligence as your
          team grows.
        </p>
      </div>
    </section>
  );
}
