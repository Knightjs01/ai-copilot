import Link from "next/link";
import { ArrowRight, Eye, IdCard, LayoutGrid, Sparkles } from "lucide-react";

const PRODUCTS = [
  {
    icon: IdCard,
    name: "Phantom Passport",
    tagline: "The identity layer.",
    body: "A reusable, verified, anonymous professional profile that puts candidates in control.",
    href: "/passport",
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
              One Hiring Platform
            </h2>
          </div>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Phantom combines a verified candidate identity, an anonymous talent network, a
            complete ATS and AI-powered intelligence, so you can discover, attract and hire the
            best talent, privately.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {PRODUCTS.map((product) => (
            <div
              key={product.name}
              className="flex flex-col gap-3 rounded-2xl border border-border p-6"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <product.icon className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-foreground">{product.name}</h3>
                <p className="text-sm font-medium text-brand">{product.tagline}</p>
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground">{product.body}</p>
              <Link
                href={product.href}
                className="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-brand hover:text-brand/80"
              >
                Learn more
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
