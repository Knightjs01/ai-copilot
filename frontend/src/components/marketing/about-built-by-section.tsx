import { Award } from "lucide-react";

export function AboutBuiltBySection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-2xl flex-col items-center gap-4 px-6 py-16 text-center lg:py-20">
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3.5 py-1.5">
          <Award className="h-3.5 w-3.5 text-brand" />
          <span className="text-xs font-medium text-muted-foreground">Built by, not backed by</span>
        </div>
        <p className="text-lg leading-relaxed text-muted-foreground">
          Phantom Hire is built by a team of industry-leading security professionals alongside
          Talent Acquisition specialists with over ten years of hands-on hiring experience. They
          know exactly what a hiring pipeline collects, and exactly why it shouldn&apos;t keep it.
        </p>
      </div>
    </section>
  );
}
