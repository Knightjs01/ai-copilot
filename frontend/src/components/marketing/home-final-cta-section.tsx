import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";

const AUDIENCES = [
  {
    href: "/hiring-teams",
    title: "For hiring teams",
    description: "Hire privately, screen smart, leave no trace.",
  },
  {
    href: "/job-seekers",
    title: "For job seekers",
    description: "Explore your next move, quietly.",
  },
];

export function HomeFinalCtaSection() {
  return (
    <section className="border-t border-border">
      <div className="relative mx-auto flex max-w-4xl flex-col items-center gap-6 overflow-hidden px-6 py-20 text-center">
        <div className="absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand/15 blur-3xl" aria-hidden />
        <h2 className="relative text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Start hiring differently.
        </h2>
        <p className="relative max-w-lg text-lg leading-relaxed text-muted-foreground">
          Build your hiring pipeline on a platform designed to protect the people in it.
        </p>
        <div className="relative flex flex-col gap-3 sm:flex-row">
          <Button asChild variant="brand" size="lg">
            <Link href="/signup">Start hiring</Link>
          </Button>
          <Button asChild variant="secondary" size="lg">
            <Link href="/shadow/signup">Create your Passport</Link>
          </Button>
        </div>

        <div className="relative grid w-full max-w-md grid-cols-1 gap-3 pt-6 sm:grid-cols-2">
          {AUDIENCES.map((audience) => (
            <Link
              key={audience.href}
              href={audience.href}
              className="group flex flex-col gap-1 rounded-2xl border border-border bg-card p-4 text-left transition-colors hover:border-brand/40"
            >
              <span className="flex items-center justify-between gap-2 text-sm font-semibold text-foreground">
                {audience.title}
                <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </span>
              <span className="text-xs text-muted-foreground">{audience.description}</span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
