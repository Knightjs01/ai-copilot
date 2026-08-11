import {
  BrainCircuit,
  ClipboardCheck,
  Flame,
  LayoutDashboard,
  ScrollText,
  Sparkles,
  Users,
  Vault,
} from "lucide-react";

const FEATURES = [
  {
    icon: Sparkles,
    title: "AI Hiring Blueprint",
    body: "Turns a job description into a structured brief: must-haves, nice-to-haves, and what good actually looks like.",
  },
  {
    icon: BrainCircuit,
    title: "Candidate Intelligence",
    body: "AI-generated highlights and skill matches for every candidate, built from a fully redacted CV.",
  },
  {
    icon: ClipboardCheck,
    title: "Pre-Screen Assessments",
    body: "Fit ratings, gaps, and suggested questions before you ever pick up the phone.",
  },
  {
    icon: Vault,
    title: "Identity Vault & Blind Hiring",
    body: "Real identities stay encrypted and Owner-gated, with every reveal logged and reasoned.",
  },
  {
    icon: Flame,
    title: "One-Click Purge",
    body: "Burn a project and everything tied to it: resumes, AI notes, identities. All destroyed for good.",
  },
  {
    icon: ScrollText,
    title: "Historic Vault & Audit Trail",
    body: "A permanent, non-identifying record of every purge and every access, proof without the exposure.",
  },
  {
    icon: Users,
    title: "Team Roles & Permissions",
    body: "Owner, Admin and Member roles decide who can reveal an identity, who can purge, and who just hires.",
  },
  {
    icon: LayoutDashboard,
    title: "Recruiter Dashboard",
    body: "Live projects, candidates in process, and a Phantom Action list of exactly what needs your attention next.",
  },
];

export function FeatureGridSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            For hiring teams
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Phantom ATS takes care of everything in the background
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            A full hiring workflow, running quietly behind every project.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="flex flex-col gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary text-foreground">
                <feature.icon className="h-5 w-5" />
              </div>
              <h3 className="text-sm font-semibold text-foreground">{feature.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{feature.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
