import Link from "next/link";

import { Button } from "@/components/ui/button";

export function AiFinalCtaSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-6 py-20 text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Give your recruiters an AI that shows its work.
        </h2>
        <p className="max-w-lg text-lg leading-relaxed text-muted-foreground">
          Evidence-based assessments before every call, honest handoffs after every one.
        </p>
        <Button asChild variant="brand" size="lg">
          <Link href="/signup">Start hiring with Phantom</Link>
        </Button>
      </div>
    </section>
  );
}
