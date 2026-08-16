import { TalentMemoryMockup } from "@/components/marketing/mockups/talent-memory-mockup";
import { Badge } from "@/components/ui/badge";

// Talent Memory has no backend implementation today — this page is framed honestly as a
// preview/roadmap item throughout, matching the homepage's TalentMemoryBeatSection.
export function TalentMemoryHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              Talent Memory
            </p>
            <Badge variant="outline">Preview</Badge>
          </div>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Remember great talent without keeping everything forever.
          </h1>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Today, a closed project&apos;s CVs, notes, and transcripts can be purged entirely.
            What we&apos;re building next: a permitted, consent-respecting memory of the skills
            and match profile from people worth rediscovering — so a closed search doesn&apos;t
            mean starting from zero next time.
          </p>
        </div>

        <TalentMemoryMockup />
      </div>
    </section>
  );
}
