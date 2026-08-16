export function AboutHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-20 text-center lg:py-28">
        <p className="text-xs font-semibold uppercase tracking-wide text-brand">About</p>
        <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
          We think hiring collects too much, and forgets too little.
        </h1>
        <p className="text-lg leading-relaxed text-muted-foreground">
          Most hiring platforms keep everything by default: names, CVs, notes, transcripts, long
          after anyone needed them. We built Phantom around the opposite instinct. Identity stays
          with the candidate until they choose to reveal it. AI shows its evidence instead of a
          verdict. Data that isn&apos;t needed doesn&apos;t get kept.
        </p>
        <p className="text-lg leading-relaxed text-muted-foreground">
          Not because privacy is a feature we added, but because it&apos;s the reason the product
          exists at all.
        </p>
      </div>
    </section>
  );
}
