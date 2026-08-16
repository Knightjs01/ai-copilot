import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { RevealIdentityMockup } from "@/components/marketing/mockups/reveal-identity-mockup";
import { Badge } from "@/components/ui/badge";
import { ROLE_LABEL, ROLE_VARIANT } from "@/lib/status-display";
import type { RoleName } from "@/lib/types";

const ROLES: Array<{ role: RoleName; description: string }> = [
  { role: "Owner", description: "Full access, including revealing a candidate's real identity." },
  { role: "Admin", description: "Runs projects and manages the team, without identity reveal." },
  { role: "Member", description: "Scoped to the projects they've been added to." },
];

export function AtsGovernanceSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">Governance</p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Everyone sees exactly what they should.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            A candidate&apos;s real identity stays sealed until an Owner reveals it, with a
            stated reason, logged to the audit trail. Every teammate&apos;s role decides what
            they can see and do inside a project.
          </p>

          <div className="flex flex-col gap-2.5">
            {ROLES.map((item) => (
              <div
                key={item.role}
                className="flex items-start gap-3 rounded-xl border border-border bg-card p-3.5"
              >
                <Badge variant={ROLE_VARIANT[item.role]} className="mt-0.5 shrink-0">
                  {ROLE_LABEL[item.role]}
                </Badge>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </div>
            ))}
          </div>

          <Link
            href="/trust"
            className="flex items-center gap-1 text-sm font-medium text-brand hover:underline"
          >
            See the full security architecture
            <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <RevealIdentityMockup />
      </div>
    </section>
  );
}
