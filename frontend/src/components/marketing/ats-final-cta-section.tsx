import Link from "next/link";

import { Button } from "@/components/ui/button";

export function AtsFinalCtaSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-6 py-20 text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Give your team an ATS with a brain.
        </h2>
        <p className="max-w-lg text-lg leading-relaxed text-muted-foreground">
          Real pipelines, real AI fit ratings, and a dashboard that tells you what needs your
          attention next.
        </p>
        <Button asChild variant="brand" size="lg">
          <Link href="/signup">Start hiring with Phantom</Link>
        </Button>
      </div>
    </section>
  );
}
