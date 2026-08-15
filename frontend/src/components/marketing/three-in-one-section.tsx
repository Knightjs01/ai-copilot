import Image from "next/image";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";

interface Pillar {
  title: string;
  subtitle: string;
  body: string;
  status: "Live now" | "Coming soon";
  image: { src: string; alt: string };
  href: string;
  cta: string;
}

const PILLARS: Pillar[] = [
  {
    image: { src: "/shadow-icon.png", alt: "" },
    title: "Shadow Job Board",
    subtitle: "The anonymous job board",
    body: "Where candidates discover and apply to roles under a Callsign, not a name, staying in the shadows until they choose to step forward.",
    status: "Live now",
    href: "/job-seekers",
    cta: "Explore Shadow",
  },
  {
    image: { src: "/phantom-icon.png", alt: "" },
    title: "Phantom ATS",
    subtitle: "Your hiring pipeline, end to end",
    body: "Hiring projects, candidate tracking, roles and permissions: the pipeline your team already runs on, built around Zero-Retention from day one.",
    status: "Live now",
    href: "/hiring-teams",
    cta: "Explore Phantom ATS",
  },
  {
    image: { src: "/phantom-ghost-hero.png", alt: "" },
    title: "Phantom AI",
    subtitle: "The AI Assistant",
    body: "Reads job descriptions, screens candidates, drafts questions, and briefs the hiring manager, automatically, in the background.",
    status: "Live now",
    href: "/#phantom",
    cta: "Meet Phantom",
  },
];

export function ThreeInOneSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            Three core services. One platform.
          </h2>
          <p className="mt-3 text-muted-foreground">
            Most tools make you stitch these together yourself. Phantom Hire doesn&apos;t.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-3">
          {PILLARS.map((pillar) => (
            <div
              key={pillar.title}
              className="relative flex flex-col gap-3 overflow-hidden rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]"
            >
              <Image
                src={pillar.image.src}
                alt={pillar.image.alt}
                width={200}
                height={200}
                className="pointer-events-none absolute -right-8 -top-8 h-36 w-36 object-contain opacity-25"
              />
              <div className="relative flex items-center justify-between">
                <Badge variant={pillar.status === "Live now" ? "success" : "outline"}>
                  {pillar.status}
                </Badge>
              </div>
              <div className="relative">
                <h3 className="text-base font-semibold text-foreground">{pillar.title}</h3>
                <p className="text-xs font-medium text-brand">{pillar.subtitle}</p>
              </div>
              <p className="relative text-sm leading-relaxed text-muted-foreground">
                {pillar.body}
              </p>
              <Link
                href={pillar.href}
                className="relative mt-1 inline-flex items-center gap-1.5 text-sm font-medium text-brand hover:underline"
              >
                {pillar.cta}
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
