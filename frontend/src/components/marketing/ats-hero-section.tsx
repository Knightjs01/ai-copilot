import Image from "next/image";
import Link from "next/link";
import { KeyRound, ShieldCheck, Users, Workflow } from "lucide-react";

import { AtsAppShellMockup } from "@/components/marketing/mockups/ats-app-shell-mockup";
import { Button } from "@/components/ui/button";

const FEATURES = [
  {
    icon: Workflow,
    title: "Hiring projects",
    body: "One real pipeline per role, whether candidates came from Shadow or were added directly.",
  },
  {
    icon: ShieldCheck,
    title: "AI fit rating",
    body: "Every candidate rated Strong, Good, Possible, or Weak Fit, with the evidence attached.",
  },
  {
    icon: KeyRound,
    title: "Identity Vault",
    body: "Real identity stays sealed until an Owner reveals it, with a stated reason, logged.",
  },
  {
    icon: Users,
    title: "Team & roles",
    body: "Owner, Admin, and Member roles decide exactly what each teammate can see and do.",
  },
];

export function AtsHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-16 lg:py-20">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
          <div className="flex flex-col gap-5">
            <div className="flex items-center gap-2">
              <Image
                src="/phantom-icon.png"
                alt=""
                width={234}
                height={190}
                className="h-4 w-auto"
              />
              <p className="text-xs font-semibold uppercase tracking-wide text-brand">
                Phantom ATS
              </p>
            </div>
            <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
              Every candidate ranked by evidence.
            </h1>
            <p className="text-lg leading-relaxed text-muted-foreground">
              Hiring projects, Callsigns instead of names, AI fit ratings, and a live dashboard of
              exactly what needs your attention next. Dense, organised, and built for the team
              that lives inside it every day.
            </p>
            <div>
              <Button asChild variant="brand" size="lg">
                <Link href="/signup">Start hiring with Phantom</Link>
              </Button>
            </div>
          </div>

          <AtsAppShellMockup />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="flex flex-col gap-2.5 rounded-2xl border border-border bg-card p-5 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <feature.icon className="h-4 w-4" />
              </div>
              <p className="text-sm font-semibold text-foreground">{feature.title}</p>
              <p className="text-sm leading-relaxed text-muted-foreground">{feature.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
