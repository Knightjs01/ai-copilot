import { Bot, EyeOff, KanbanSquare } from "lucide-react";

import { Badge } from "@/components/ui/badge";

const PILLARS = [
  {
    icon: EyeOff,
    title: "Shadow",
    subtitle: "The anonymous job board",
    body: "Where candidates discover and apply to roles under a Callsign, not a name — staying in the shadows until they choose to step forward.",
    status: "Coming soon" as const,
  },
  {
    icon: KanbanSquare,
    title: "Talent ATS",
    subtitle: "Your hiring pipeline, end to end",
    body: "Hiring projects, candidate tracking, roles and permissions — the pipeline your team already runs on, built around Zero-Retention from day one.",
    status: "Live now" as const,
  },
  {
    icon: Bot,
    title: "Phantom",
    subtitle: "The AI Assistant",
    body: "Reads job descriptions, screens candidates, drafts questions, and briefs the hiring manager — automatically, in the background.",
    status: "Live now" as const,
  },
];

export function ThreeInOneSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            Three core services. One platform.
          </h2>
          <p className="mt-3 text-muted-foreground">
            Most tools make you stitch these together yourself. Phantom Hire doesn&apos;t.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-3">
          {PILLARS.map((pillar) => (
            <div
              key={pillar.title}
              className="flex flex-col gap-3 rounded-2xl border border-border bg-white p-6 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex items-center justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
                  <pillar.icon className="h-5 w-5" />
                </div>
                <Badge variant={pillar.status === "Live now" ? "success" : "outline"}>
                  {pillar.status}
                </Badge>
              </div>
              <div>
                <h3 className="text-base font-semibold text-foreground">{pillar.title}</h3>
                <p className="text-xs font-medium text-brand">{pillar.subtitle}</p>
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground">{pillar.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
