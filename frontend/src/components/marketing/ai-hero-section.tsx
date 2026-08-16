import Image from "next/image";
import Link from "next/link";

import { AiLifecycleMockup } from "@/components/marketing/mockups/ai-lifecycle-mockup";
import { Button } from "@/components/ui/button";

export function AiHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <div className="flex items-center gap-2">
            <Image src="/phantom-icon.png" alt="" width={234} height={190} className="h-4 w-auto" />
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">Phantom AI</p>
          </div>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            AI that shows its work.
          </h1>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Generated on demand from the role brief and the candidate&apos;s own record. Every
            output comes with its evidence attached. No black-box score, no live listening in on
            your calls.
          </p>
          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring with Phantom</Link>
            </Button>
          </div>
        </div>

        <AiLifecycleMockup />
      </div>
    </section>
  );
}
