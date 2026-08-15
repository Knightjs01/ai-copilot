import { EyeOff } from "lucide-react";

const USE_CASES = [
  "Executive & Leadership Search",
  "Confidential Replacement Hires",
  "Government & Defense",
  "Financial Services & Legal",
  "M&A and Restructuring",
  "Competitor-Sensitive Roles",
  "Stealth-Mode Startups",
];

export function DiscreetIndustriesSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-4xl px-6 py-16 text-center lg:py-20">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand/10 text-brand">
          <EyeOff className="h-6 w-6" />
        </div>
        <h2 className="mt-5 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Built for hiring that can&apos;t be seen
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
          Phantom Hire was designed for the moments a hire can&apos;t hit the grapevine: a
          confidential leadership change, a sensitive government role, a poach from a rival, a
          restructuring the market isn&apos;t ready for yet.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-2.5">
          {USE_CASES.map((useCase) => (
            <span
              key={useCase}
              className="rounded-full border border-border bg-card px-4 py-1.5 text-sm text-foreground"
            >
              {useCase}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
