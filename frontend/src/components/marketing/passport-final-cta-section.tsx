import Link from "next/link";

import { Button } from "@/components/ui/button";

export function PassportFinalCtaSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-6 py-20 text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Build your Passport once. Use it everywhere.
        </h2>
        <p className="max-w-lg text-lg leading-relaxed text-muted-foreground">
          Free forever. Private by default. Yours to control.
        </p>
        <Button asChild variant="brand" size="lg">
          <Link href="/shadow/signup">Build your Passport</Link>
        </Button>
      </div>
    </section>
  );
}
