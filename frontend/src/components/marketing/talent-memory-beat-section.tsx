import Image from "next/image";

import { TalentMemoryMockup } from "@/components/marketing/mockups/talent-memory-mockup";
import { Badge } from "@/components/ui/badge";

// Talent Memory has no backend implementation today — this beat is framed honestly as a
// preview/roadmap item, not live product, per the redesign's decision on unbuilt features.
export function TalentMemoryBeatSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="order-2 lg:order-1">
          <TalentMemoryMockup />
        </div>

        <div className="order-1 flex flex-col gap-5 lg:order-2">
          <div className="flex items-center gap-2">
            <Image src="/phantom-icon.png" alt="" width={234} height={190} className="h-4 w-auto" />
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              Talent Memory
            </p>
            <Badge variant="outline">Preview</Badge>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Remember great talent without keeping everything forever.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            When a project closes, its CVs, notes, and transcripts can be purged entirely. What
            we&apos;re building next: a permitted, consent-respecting memory of the skills and
            match profile from the people worth rediscovering, so a closed search doesn&apos;t
            mean starting from zero next time.
          </p>
        </div>
      </div>
    </section>
  );
}
