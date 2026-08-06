import Link from "next/link";
import { Award, KeyRound, Lock, ShieldCheck, UserCog, Users } from "lucide-react";

import { Button } from "@/components/ui/button";

const SECURITY_POINTS = [
  {
    icon: Lock,
    title: "Vault-encrypted identities",
    body: "Candidate PII never sits in the day-to-day workspace — it's encrypted the moment it's collected.",
  },
  {
    icon: UserCog,
    title: "Owner-gated reveals",
    body: "Only an Owner can reveal a candidate's identity, and only with a reason recorded against their name.",
  },
  {
    icon: Users,
    title: "Role-based access",
    body: "Owner, Admin and Member roles decide exactly what each person on your team can see and do.",
  },
  {
    icon: KeyRound,
    title: "Tenant-isolated by design",
    body: "Every query is scoped to your company at the database level — there's no shared table to misconfigure.",
  },
];

export function SecurityCtaSection() {
  return (
    <section id="security" className="border-t border-border bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-20 lg:py-28">
        <div className="mx-auto max-w-2xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-white px-3.5 py-1.5">
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
            Talent Acquisition specialists with over ten years of hands-on hiring experience —
            people who know exactly what a hiring pipeline collects, and exactly why it
            shouldn&apos;t keep it.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {SECURITY_POINTS.map((point) => (
            <div
              key={point.title}
              className="flex flex-col gap-3 rounded-2xl border border-border bg-white p-6 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <point.icon className="h-5 w-5" />
              </div>
              <h3 className="text-sm font-semibold text-foreground">{point.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{point.body}</p>
            </div>
          ))}
        </div>

        <div className="mt-16 flex flex-col items-center gap-5 rounded-3xl border border-border bg-white px-8 py-14 text-center shadow-sm shadow-slate-900/[0.03]">
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
