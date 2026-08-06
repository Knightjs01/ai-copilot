import { Bot, Briefcase, KanbanSquare } from "lucide-react";

import { Badge } from "@/components/ui/badge";

const PILLARS = [
  {
    icon: Briefcase,
    title: "Job Board",
    body: "Where candidates discover and apply to your roles — under a Callsign, not a name, from the moment they land on it.",
    status: "Coming soon" as const,
  },
  {
    icon: KanbanSquare,
    title: "ATS",
    body: "The pipeline your team already runs on: hiring projects, candidate tracking, roles, permissions — end to end.",
    status: "Live now" as const,
  },
  {
    icon: Bot,
    title: "Hiring Phantom Assistant",
    body: "The AI that reads job descriptions, screens candidates, drafts questions, and briefs the hiring manager — automatically.",
    status: "Live now" as const,
  },
];

export function ThreeInOneSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            One platform. Job board, ATS, and AI hiring assistant — together.
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
              <h3 className="text-base font-semibold text-foreground">{pillar.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{pillar.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
