import Link from "next/link";

import { Button } from "@/components/ui/button";

export function TalentMemoryFinalCtaSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-6 py-20 text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Start hiring on the platform Talent Memory is being built into.
        </h2>
        <p className="max-w-lg text-lg leading-relaxed text-muted-foreground">
          Everything Phantom does today already respects the same principle: only keep what you
          have permission to keep.
        </p>
        <Button asChild variant="brand" size="lg">
          <Link href="/signup">Start hiring with Phantom</Link>
        </Button>
      </div>
    </section>
  );
}
