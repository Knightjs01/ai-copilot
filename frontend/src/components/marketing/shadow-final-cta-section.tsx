import Link from "next/link";

import { Button } from "@/components/ui/button";

export function ShadowFinalCtaSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-6 py-20 text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Enter the market without stepping into the light.
        </h2>
        <p className="max-w-lg text-lg leading-relaxed text-muted-foreground">
          Free for candidates, forever. Built for companies running a search that needs to stay
          quiet.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Button asChild variant="brand" size="lg">
            <Link href="/shadow">Browse the board</Link>
          </Button>
          <Button asChild variant="secondary" size="lg">
            <Link href="/signup">Post a role</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
