import Link from "next/link";

import { Button } from "@/components/ui/button";

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
      </div>
    </section>
  );
}
