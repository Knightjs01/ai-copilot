import { BrainCircuit, ClipboardList, Target } from "lucide-react";

const CAPABILITIES = [
  {
    icon: ClipboardList,
    name: "Hiring Blueprint",
    description: "Generated from the role brief: what the role actually needs, structured.",
    fields: ["must_have_qualifications", "nice_to_have_qualifications", "evaluation_criteria"],
  },
  {
    icon: BrainCircuit,
    name: "Intelligence Pack",
    description: "Generated from the candidate's own record: skills, experience, and highlights.",
    fields: ["skills", "experience_summary", "highlights"],
  },
  {
    icon: Target,
    name: "Prescreen Assessment",
    description: "Generated from both: an evidence-based fit rating, on demand, before the call.",
    fields: ["fit_rating", "strengths", "gaps", "suggested_questions"],
  },
];

export function AiCapabilitiesSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Where Phantom AI works
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Three real outputs, not one gimmick.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Phantom AI runs at three real points in the hiring process. Each one is generated on
            demand from real data already in the system, never invented.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          {CAPABILITIES.map((capability) => (
            <div
              key={capability.name}
              className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <capability.icon className="h-5 w-5" />
              </div>
              <div className="flex flex-col gap-1.5">
                <p className="text-sm font-semibold text-foreground">{capability.name}</p>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {capability.description}
                </p>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {capability.fields.map((field) => (
                  <span
                    key={field}
                    className="rounded-full border border-border bg-secondary/40 px-2.5 py-1 font-mono text-[10px] text-muted-foreground"
                  >
                    {field}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
