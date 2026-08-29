import Link from "next/link";
import { ArrowRight, Eye, IdCard, LayoutGrid, Sparkles } from "lucide-react";

import { cn } from "@/lib/utils";

const PRODUCTS = [
  {
    icon: IdCard,
    name: "Phantom Passport",
    tagline: "The identity layer.",
    body: "A reusable, verified, anonymous professional profile that puts candidates in control.",
    href: "/passport",
    // The flagship, candidate-facing product -- given a distinct colored treatment below so it
    // reads as the core feature of the ecosystem, not just one of four equal tiles.
    featured: true,
  },
  {
    icon: Eye,
    name: "Shadow",
    tagline: "The talent network.",
    body: "Discover exceptional candidates and opportunities without the exposure of traditional job boards.",
    href: "/shadow-job-board",
  },
  {
    icon: LayoutGrid,
    name: "Phantom ATS",
    tagline: "The hiring workspace.",
    body: "Manage your entire hiring pipeline with collaborative workflows, from discovery to decision.",
    href: "/ats",
  },
  {
    icon: Sparkles,
    name: "Phantom AI",
    tagline: "The intelligence layer.",
    body: "Turn evidence into better hiring decisions with AI throughout the platform.",
    href: "/ai",
  },
];

export function ProductEcosystemSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              The Phantom ecosystem
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              Four Layers
              <br />
              <span className="text-brand">One Hiring Platform</span>
            </h2>
          </div>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Phantom combines a verified candidate identity, an anonymous talent network, a
            complete ATS and AI-powered intelligence, so you can discover, attract and hire the
            best talent, privately.
          </p>
        </div>

        <div className="relative mt-14">
          {/* Decorative connecting thread behind the row -- desktop only, hidden once the grid
              stacks below lg so it never has to track a layout it doesn't match. */}
          <div className="pointer-events-none absolute inset-x-8 top-8 hidden h-px bg-gradient-to-r from-brand/0 via-brand/25 to-electric/0 lg:block" />

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {PRODUCTS.map((product, index) => (
              <div
                key={product.name}
                className={cn(
                  "relative flex flex-col gap-3 rounded-2xl p-6",
                  product.featured
                    ? "bg-gradient-to-br from-brand to-electric text-brand-foreground shadow-xl shadow-brand/25"
                    : "border border-border bg-background"
                )}
              >
                <span
                  className={cn(
                    "absolute right-5 top-5 text-xs font-bold tracking-wide",
                    product.featured ? "text-brand-foreground/60" : "text-muted-foreground/70"
                  )}
                >
                  0{index + 1}
                </span>

                <div
                  className={cn(
                    "flex h-14 w-14 items-center justify-center rounded-xl",
                    product.featured
                      ? "bg-white/15 text-brand-foreground"
                      : "bg-gradient-to-br from-brand to-electric text-white shadow-lg shadow-brand/30"
                  )}
                >
                  <product.icon className="h-6 w-6" />
                </div>

                <div>
                  <h3
                    className={cn(
                      "text-base font-semibold",
                      product.featured ? "text-brand-foreground" : "text-foreground"
                    )}
                  >
                    {product.name}
                  </h3>
                  <p
                    className={cn(
                      "text-sm font-medium",
                      product.featured ? "text-brand-foreground/90" : "text-brand"
                    )}
                  >
                    {product.tagline}
                  </p>
                </div>

                <p
                  className={cn(
                    "flex-1 text-sm leading-relaxed",
                    product.featured ? "text-brand-foreground/80" : "text-muted-foreground"
                  )}
                >
                  {product.body}
                </p>

                <Link
                  href={product.href}
                  className={cn(
                    "mt-2 inline-flex items-center gap-1.5 text-sm font-medium",
                    product.featured
                      ? "text-brand-foreground hover:text-brand-foreground/80"
                      : "text-brand hover:text-brand/80"
                  )}
                >
                  Learn more
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
