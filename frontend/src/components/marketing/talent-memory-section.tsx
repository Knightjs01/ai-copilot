import { Badge } from "@/components/ui/badge";
import { Spectre482Mockup } from "@/components/marketing/mockups/spectre-482-mockup";
import { TalentMemoryMockup } from "@/components/marketing/mockups/talent-memory-mockup";

export function TalentMemorySection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
          <div className="flex flex-col gap-5">
            <div className="flex items-center gap-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-brand">
                Talent Memory
              </p>
              <Badge variant="outline" className="text-[10px]">
                Preview
              </Badge>
            </div>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              Your projects can disappear. Your talent intelligence doesn&apos;t have to.
            </h2>
            <p className="text-lg leading-relaxed text-muted-foreground">
              Traditional ATS platforms store everything forever. Phantom separates
              project-specific data, CVs, interview notes, transcripts, AI context and personal
              information, from persistent talent intelligence: skills, experience, match
              profile, relationship and consent state. When a project closes, the project data
              can be permanently destroyed, where permitted and configured, according to your
              organisation&apos;s retention policy.
            </p>
          </div>
          <TalentMemoryMockup />
        </div>

        <div className="mt-16 grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
          <div className="order-2 lg:order-1">
            <Spectre482Mockup />
          </div>
          <div className="order-1 flex flex-col gap-5 lg:order-2">
            <div className="flex items-center gap-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-brand">
                Phantom remembers great talent
              </p>
              <Badge variant="outline" className="text-[10px]">
                Preview
              </Badge>
            </div>
            <h3 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
              Open a role. Phantom will already know who fits.
            </h3>
            <p className="text-lg leading-relaxed text-muted-foreground">
              The direction we&apos;re building toward: candidates your organisation has
              previously assessed stay discoverable through Talent Memory, without their
              project-specific data or identity ever being retained. Not available today.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
