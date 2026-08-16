import Link from "next/link";

import { ShadowBoardShellMockup } from "@/components/marketing/mockups/shadow-board-shell-mockup";
import { Button } from "@/components/ui/button";

export function ShadowHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Shadow Job Board
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            The job market you can enter without being seen.
          </h1>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Search real roles by skill, not by title. Salary shown upfront. Apply with your
            Phantom Passport and companies see your experience, not your name, until you choose
            to reveal it.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button asChild variant="brand" size="lg">
              <Link href="/shadow">Browse the board</Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <Link href="/signup">Post a role</Link>
            </Button>
          </div>
        </div>

        <ShadowBoardShellMockup />
      </div>
    </section>
  );
}
