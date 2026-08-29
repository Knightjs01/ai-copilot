"use client";

import * as React from "react";
import { KeyRound, ShieldCheck } from "lucide-react";

import { CandidateMfaDisableDialog } from "@/components/shadow/candidate-mfa-disable-dialog";
import { CandidateMfaSetupDialog } from "@/components/shadow/candidate-mfa-setup-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCandidateAuth } from "@/lib/candidate-auth-context";

// Mirrors (app)/security/page.tsx (the company equivalent), minus the Sessions card -- not asked
// for here and candidate sessions aren't otherwise surfaced anywhere in Shadow today. MFA is
// opt-in: there's no enrollment deadline enforced (see candidate_auth/dependencies.py's
// require_candidate_mfa_enrolled docstring for why), so this reads as an invitation, not a
// countdown.
export default function ShadowSecurityPage() {
  const { candidate } = useCandidateAuth();
  const [setupOpen, setSetupOpen] = React.useState(false);
  const [disableOpen, setDisableOpen] = React.useState(false);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Security</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage how you sign in to your Phantom Passport.
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-muted-foreground" />
            <CardTitle>Multi-factor authentication</CardTitle>
          </div>
          {candidate?.mfa_enabled ? (
            <Badge variant="success">Enabled</Badge>
          ) : (
            <Badge variant="outline">Not enabled</Badge>
          )}
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {candidate?.mfa_enabled
              ? "Your account requires a one-time code from an authenticator app in addition to your password."
              : "Add a one-time code from an authenticator app as a second step at login, on top of your password. Optional — turn it on whenever you'd like the extra protection."}
          </p>
          <div className="mt-4">
            {candidate?.mfa_enabled ? (
              <Button type="button" variant="secondary" onClick={() => setDisableOpen(true)}>
                Disable MFA
              </Button>
            ) : (
              <Button type="button" variant="brand" onClick={() => setSetupOpen(true)}>
                <ShieldCheck className="h-3.5 w-3.5" />
                Enable MFA
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <CandidateMfaSetupDialog open={setupOpen} onOpenChange={setSetupOpen} />
      <CandidateMfaDisableDialog open={disableOpen} onOpenChange={setDisableOpen} />
    </div>
  );
}
