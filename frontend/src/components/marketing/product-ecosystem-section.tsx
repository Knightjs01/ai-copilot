import Link from "next/link";
import {
  ArrowRight,
  BrainCircuit,
  Eye,
  Globe,
  LayoutGrid,
  Lock,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";

import { cn } from "@/lib/utils";

const PRODUCTS = [
  {
    icon: ShieldCheck,
    name: "Phantom Passport",
    tagline: "The identity layer.",
    body: "A verified, anonymous candidate profile. Built once, used to apply everywhere.",
    href: "/passport",
    // The flagship, candidate-facing product -- given a distinct gold/dark treatment below so it
    // reads as the core feature of the ecosystem, not just one of five equal tiles.
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
    icon: Users,
    name: "Phantom Talent Partners",
    tagline: "The expert layer.",
    body: "Access verified recruitment experts who manage your search using our network, technology and insights.",
    href: "/talent-partners",
  },
  {
    icon: Sparkles,
    name: "Phantom AI",
    tagline: "The intelligence layer.",
    body: "The whole platform is underpinned by Phantom AI, turning evidence into better hiring decisions.",
    href: "/ai",
  },
];

const TRUST_POINTS = [
  {
    icon: Lock,
    title: "End-to-end anonymity",
    body: "Keeps identities private until the right moment.",
  },
  {
    icon: ShieldCheck,
    title: "Verified identities",
    body: "Evidence-based verification you can trust.",
  },
  {
    icon: TrendingUp,
    title: "Evidence-based insights",
    body: "Make confident decisions with real data.",
  },
  {
    icon: Globe,
    title: "Enterprise-grade security",
    body: "Built with privacy, compliance and security at its core.",
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
              Five Layers.
              <br />
              <span className="text-brand">One Hiring Platform.</span>
            </h2>
            <p className="mt-4 max-w-md text-sm text-muted-foreground">
              Everything you need to discover, engage and hire exceptional talent, privately.
            </p>
          </div>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Phantom combines a verified candidate identity, an anonymous talent network, a
            complete ATS, expert recruitment partners and AI-powered intelligence —{" "}
            <span className="font-semibold text-foreground">all in one secure platform.</span>
          </p>
        </div>

        <div className="relative mt-14">
          {/* Decorative connecting thread behind the row -- desktop only, hidden once the grid
              stacks below lg so it never has to track a layout it doesn't match. */}
          <div className="pointer-events-none absolute inset-x-8 top-8 hidden h-px bg-gradient-to-r from-brand/0 via-brand/25 to-electric/0 lg:block" />

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-5">
            {PRODUCTS.map((product, index) => (
              <div
                key={product.name}
                className={cn(
                  "relative flex flex-col gap-2.5 rounded-2xl p-5",
                  product.featured
                    ? "bg-gradient-to-br from-foreground to-brand text-brand-foreground shadow-xl shadow-brand/25"
                    : "border border-border bg-background"
                )}
              >
                <div className="flex items-start justify-between">
                  <div
                    className={cn(
                      "flex h-11 w-11 items-center justify-center rounded-xl",
                      product.featured ? "bg-gold/20 text-gold" : "bg-brand/10 text-brand"
                    )}
                  >
                    <product.icon className="h-5 w-5" />
                  </div>
                  <span
                    className={cn(
                      "text-xs font-bold tracking-wide",
                      product.featured ? "text-brand-foreground/50" : "text-muted-foreground/70"
                    )}
                  >
                    0{index + 1}
                  </span>
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
                      product.featured ? "text-brand-foreground" : "text-brand"
                    )}
                  >
                    {product.tagline}
                  </p>
                </div>

                <p
                  className={cn(
                    "text-sm leading-relaxed",
                    product.featured ? "text-brand-foreground/80" : "text-muted-foreground"
                  )}
                >
                  {product.body}
                </p>

                {product.featured && (
                  <span className="inline-flex w-fit items-center gap-1.5 rounded-full border border-gold/40 px-3 py-1 text-xs font-medium text-brand-foreground">
                    <ShieldCheck className="h-3 w-3" />
                    Verified. Private. Portable.
                  </span>
                )}

                <Link
                  href={product.href}
                  className={cn(
                    "mt-auto inline-flex items-center gap-1.5 text-sm font-medium",
                    product.featured
                      ? "text-gold hover:text-gold/80"
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

        <div className="mt-8 flex flex-col gap-8 rounded-2xl border border-border bg-background p-6 sm:p-8 lg:flex-row lg:items-center lg:gap-10">
          <div className="flex items-start gap-4 lg:max-w-xs lg:shrink-0">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gold/10 text-gold">
              <BrainCircuit className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground">Powered by Phantom AI</h3>
              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                From matching and candidate intelligence to workflow automation and decision
                support, Phantom AI connects every layer of the platform to deliver better hiring
                outcomes.
              </p>
            </div>
          </div>

          <div className="grid flex-1 grid-cols-1 gap-6 border-t border-border pt-6 sm:grid-cols-2 lg:grid-cols-4 lg:border-l lg:border-t-0 lg:pl-10 lg:pt-0">
            {TRUST_POINTS.map((point) => (
              <div key={point.title} className="flex items-start gap-3">
                <point.icon className="mt-0.5 h-4 w-4 shrink-0 text-gold" />
                <div>
                  <p className="text-sm font-semibold text-foreground">{point.title}</p>
                  <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
                    {point.body}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
