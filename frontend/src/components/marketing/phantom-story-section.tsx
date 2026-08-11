import { Ghost, Sparkles, Wand2 } from "lucide-react";

const STORY_BEATS = [
  {
    icon: Sparkles,
    title: "He appears",
    body: "The moment you open a role, Phantom steps in, reading the job description, briefing the hiring manager, and getting to work in the background.",
  },
  {
    icon: Wand2,
    title: "He helps you hire",
    body: "He screens every CV, briefs you on fit, drafts the questions worth asking, and keeps the whole team aligned, all without ever putting a name in front of you.",
  },
  {
    icon: Ghost,
    title: "He disappears",
    body: "When the role is filled, Phantom burns the project: every resume, identity and record, gone for good. He leaves behind only what compliance actually needs: a certificate and a timestamp in the vault, never a name.",
  },
];

export function PhantomStorySection() {
  return (
    <section id="phantom" className="border-t border-border bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-20 lg:py-28">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Meet Phantom
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            He isn&apos;t a mascot. He&apos;s the invisible TA partner behind every hire, and the
            whole product is built around what he does.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-8 md:grid-cols-3">
          {STORY_BEATS.map((beat, index) => (
            <div key={beat.title} className="relative flex flex-col items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand/10 text-brand">
                <beat.icon className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Step {index + 1}
                </p>
                <h3 className="mt-1 text-xl font-semibold text-foreground">{beat.title}</h3>
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground">{beat.body}</p>
            </div>
          ))}
        </div>

        <p className="mx-auto mt-14 max-w-xl text-center text-sm font-medium text-muted-foreground">
          That&apos;s not a metaphor. It&apos;s how the product actually works.
        </p>
      </div>
    </section>
  );
}
