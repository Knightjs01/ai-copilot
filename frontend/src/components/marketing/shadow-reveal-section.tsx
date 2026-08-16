import { ShadowRevealRequestMockup } from "@/components/marketing/mockups/shadow-reveal-request-mockup";

export function ShadowRevealSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Reveal Requests, candidate-controlled
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            A company can ask. Only you can answer.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            When a company wants to move forward, they send a Reveal Request with a stated
            reason, not a blanket unmasking. You see exactly why they&apos;re asking and approve
            or decline it yourself, every time. This is separate from an internal team&apos;s own
            identity vault reveal — here, the choice always sits with you.
          </p>
        </div>

        <ShadowRevealRequestMockup />
      </div>
    </section>
  );
}
