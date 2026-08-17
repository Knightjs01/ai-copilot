import { CheckCircle2 } from "lucide-react";

const BENEFITS = [
  "Build once, apply everywhere under an anonymous Callsign.",
  "Private by default. Nobody sees your name or current employer until you decide they should.",
  "You control every version and every reveal. Nothing goes out, and nothing is disclosed, without your explicit approval.",
  "Free, permanently. There's no paid tier for candidates — the Passport was never going to be something you buy your way into.",
];

export function PassportBenefitsSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-4xl flex-col gap-8 px-6 py-16 lg:py-20">
        <div className="flex flex-col gap-5 text-center">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Why build one
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            A record that works for you, not against you.
          </h2>
        </div>

        <ul className="flex flex-col gap-4">
          {BENEFITS.map((benefit) => (
            <li key={benefit} className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
              <span className="text-base leading-relaxed text-foreground/80">{benefit}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
