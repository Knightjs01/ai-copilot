import Link from "next/link";
import {
  Award,
  Briefcase,
  CheckCircle2,
  EyeOff,
  KeyRound,
  Lock,
  ShieldCheck,
  UserCog,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";

const SECURITY_POINTS = [
  {
    icon: Lock,
    title: "Vault-encrypted identities",
    body: "Candidate PII never sits in the day-to-day workspace. It's encrypted the moment it's collected.",
  },
  {
    icon: UserCog,
    title: "Owner-gated reveals",
    body: "Only an Owner can reveal a candidate's identity, and only with a reason recorded against their name.",
  },
  {
    icon: Users,
    title: "Role-based access",
    body: "Five distinct roles, from Owner to Interviewer, decide exactly what each person on your team can see and do.",
  },
  {
    icon: KeyRound,
    title: "Tenant-isolated by design",
    body: "Every query is scoped to your company at the database level, with no shared table to misconfigure.",
  },
];

const ATS_BENEFITS = [
  "End-to-end encrypted workflow. Every candidate record moves through your pipeline encrypted at rest, decrypted only for an Owner, only for a stated reason, only for as long as it takes.",
  "Fit ranking your team can trust at a glance. Every candidate is scored Strong, Good, Possible or Weak Fit the moment their CV lands, so screening time goes to the right conversations first.",
  "Nothing left to subpoena. When a search closes, there's no residual database of names, CVs or notes sitting around waiting to become tomorrow's liability.",
  "Zero-Trust access as standard. Every teammate signs in with MFA, and high-risk moves like revealing an identity, purging a project, or inviting a teammate require a fresh password-and-code check, no exceptions. See, and revoke, every signed-in device from your Security Centre.",
];

const CANDIDATE_BENEFITS = [
  "A Passport, not a profile. Your Phantom Passport travels with you across every role you explore, private by default, revealed only when you choose.",
  "Matched on skill, not visibility. AI matching finds roles that fit what you can actually do, not what a keyword search happens to catch.",
  "Explore under Shadow, our anonymous talent network, where you exist as a Callsign until the moment you decide to step forward.",
  "Verification without exposure, on the roadmap: reusable, cryptographic credential checks, so you prove you're qualified without re-submitting sensitive documents to every company you talk to.",
];

export function SecurityCtaSection() {
  return (
    <section id="security" className="border-t border-border bg-secondary/20">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3.5 py-1.5">
            <Award className="h-3.5 w-3.5 text-brand" />
            <span className="text-xs font-medium text-muted-foreground">
              Built by security professionals and TA specialists, not theorists
            </span>
          </div>
          <h2 className="mt-5 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Security, by the people who&apos;ve lived it
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Phantom Hire is built by a team of industry-leading security professionals alongside
            Talent Acquisition specialists with over ten years of hands-on hiring experience.
            They know exactly what a hiring pipeline collects, and exactly why it shouldn&apos;t
            keep it.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {SECURITY_POINTS.map((point) => (
            <div
              key={point.title}
              className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <point.icon className="h-5 w-5" />
              </div>
              <h3 className="text-sm font-semibold text-foreground">{point.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{point.body}</p>
            </div>
          ))}
        </div>

        <div className="mt-16">
          <div className="mx-auto max-w-2xl text-center">
            <h3 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
              Built for both sides of the hire
            </h3>
            <p className="mt-4 text-muted-foreground">
              Zero-Retention isn&apos;t a feature bolted onto a normal ATS. It&apos;s the reason
              Phantom Hire exists. The less a platform holds onto, the less there is for anyone
              to lose, leak, or misuse. Here&apos;s what that principle actually delivers,
              depending on which side of the hire you&apos;re on.
            </p>
          </div>

          <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-7 shadow-sm shadow-slate-900/[0.03]">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                  <Briefcase className="h-4 w-4" />
                </div>
                <h4 className="text-base font-semibold text-foreground">For hiring teams</h4>
              </div>
              <ul className="flex flex-col gap-3">
                {ATS_BENEFITS.map((benefit) => (
                  <li key={benefit} className="flex items-start gap-2.5">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                    <span className="text-sm leading-relaxed text-muted-foreground">
                      {benefit}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-7 shadow-sm shadow-slate-900/[0.03]">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                  <EyeOff className="h-4 w-4" />
                </div>
                <h4 className="text-base font-semibold text-foreground">For candidates</h4>
              </div>
              <ul className="flex flex-col gap-3">
                {CANDIDATE_BENEFITS.map((benefit) => (
                  <li key={benefit} className="flex items-start gap-2.5">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                    <span className="text-sm leading-relaxed text-muted-foreground">
                      {benefit}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-16 flex flex-col items-center gap-5 rounded-3xl border border-border bg-card px-8 py-14 text-center shadow-sm shadow-slate-900/[0.03]">
          <ShieldCheck className="h-8 w-8 text-brand" />
          <h2 className="max-w-xl text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            Ready to hire without the paper trail?
          </h2>
          <p className="max-w-lg text-muted-foreground">
            Bring Phantom onto your next role. He&apos;ll do the work, keep your team aligned,
            and leave nothing behind when the job is done.
          </p>
          <Button asChild variant="brand" size="lg">
            <Link href="/signup">Start hiring with Phantom</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
