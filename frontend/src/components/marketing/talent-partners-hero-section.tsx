import { Users } from "lucide-react";

export function TalentPartnersHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-16 lg:py-20">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-brand" />
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Phantom Talent Partners
          </p>
        </div>
        <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
          The expert layer of the Phantom ecosystem.
        </h1>
        <p className="max-w-2xl text-lg leading-relaxed text-muted-foreground">
          Access verified recruitment experts who manage your search using our network,
          technology and insights — working inside the same private, evidence-based platform as
          the rest of your hiring team.
        </p>
      </div>
    </section>
  );
}
