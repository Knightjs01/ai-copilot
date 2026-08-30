import { Button } from "@/components/ui/button";

export function TalentPartnersFinalCtaSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-6 py-20 text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Bring in expert help without leaving the platform.
        </h2>
        <p className="max-w-lg text-lg leading-relaxed text-muted-foreground">
          Talk to Phantom about adding a Talent Partner to your search.
        </p>
        <Button asChild variant="brand" size="lg">
          <a href="mailto:sales@phantomhire.com?subject=Phantom%20Talent%20Partners">
            Talk to Phantom
          </a>
        </Button>
      </div>
    </section>
  );
}
