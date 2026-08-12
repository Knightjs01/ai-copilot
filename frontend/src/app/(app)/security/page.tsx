"use client";

import * as React from "react";
import { KeyRound, ShieldCheck } from "lucide-react";

import { MfaDisableDialog } from "@/components/security/mfa-disable-dialog";
import { MfaSetupDialog } from "@/components/security/mfa-setup-dialog";
import { SessionsCard } from "@/components/security/sessions-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";

export default function SecurityPage() {
  const { user } = useAuth();
  const [setupOpen, setSetupOpen] = React.useState(false);
  const [disableOpen, setDisableOpen] = React.useState(false);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Security Centre
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage how you sign in and which devices have access to your account.
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-muted-foreground" />
            <CardTitle>Multi-factor authentication</CardTitle>
          </div>
          {user?.mfa_enabled ? (
            <Badge variant="success">Enabled</Badge>
          ) : (
            <Badge variant="warning">Not enabled</Badge>
          )}
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {user?.mfa_enabled
              ? "Your account requires a one-time code from an authenticator app in addition to your password."
              : "Add a one-time code from an authenticator app as a second step at login. Every account is required to enable this within a short grace period after signup."}
          </p>
          <div className="mt-4">
            {user?.mfa_enabled ? (
              <Button type="button" variant="secondary" onClick={() => setDisableOpen(true)}>
                Disable MFA
              </Button>
            ) : (
              <Button type="button" onClick={() => setSetupOpen(true)}>
                <ShieldCheck className="h-3.5 w-3.5" />
                Enable MFA
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <SessionsCard />

      <MfaSetupDialog open={setupOpen} onOpenChange={setSetupOpen} />
      <MfaDisableDialog open={disableOpen} onOpenChange={setDisableOpen} />
    </div>
  );
}
