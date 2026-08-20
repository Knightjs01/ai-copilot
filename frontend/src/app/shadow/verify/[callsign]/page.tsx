"use client";

import { useParams } from "next/navigation";
import { ShieldCheck, ShieldX } from "lucide-react";

import { ShadowTopNav } from "@/components/shadow/shadow-top-nav";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useVerifyPassport } from "@/lib/queries/phantom-passport";
import { VERIFICATION_STATUS_LABEL, VERIFICATION_STATUS_VARIANT } from "@/lib/status-display";
import styles from "../../shadow-theme.module.css";

export default function VerifyPassportPage() {
  const params = useParams<{ callsign: string }>();
  const { data: passport, isLoading } = useVerifyPassport(params.callsign);

  return (
    // ShadowTopNav + this outer bg-slate-50 gutter stay light, same pattern as every other
    // Shadow page — only <main> goes obsidian/blue.
    <div className="min-h-screen bg-slate-50">
      <ShadowTopNav />
      <main className={`${styles.shadowTheme} mx-auto max-w-2xl rounded-2xl px-6 py-10`}>
        {isLoading && (
          <div className="flex justify-center py-16">
            <Spinner className="h-6 w-6 text-muted-foreground" />
          </div>
        )}

        {!isLoading && !passport && (
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
            <ShieldX className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm font-medium text-foreground">Passport not found</p>
            <p className="max-w-xs text-sm text-muted-foreground">
              This Callsign doesn&apos;t match a real Phantom Passport.
            </p>
          </div>
        )}

        {passport && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-gold">
                Phantom Passport Verification
              </span>
              <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
                {passport.callsign}
              </h1>
              {passport.headline && (
                <p className="text-sm text-muted-foreground">{passport.headline}</p>
              )}
            </div>

            <Card>
              <CardContent className="flex flex-col gap-4 py-5">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={VERIFICATION_STATUS_VARIANT[passport.verification_status]}>
                    <ShieldCheck className="h-3 w-3" />
                    {VERIFICATION_STATUS_LABEL[passport.verification_status]}
                  </Badge>
                  {passport.seniority && <Badge variant="neutral">{passport.seniority}</Badge>}
                  <Badge variant="neutral">{passport.completion_percentage}% complete</Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  This confirms a real Phantom Passport exists behind this Callsign — it does not
                  verify identity, employment, or any specific claim.
                </p>
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
