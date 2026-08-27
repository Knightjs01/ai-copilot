"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import { PlatformAdminMfaSetupDialog } from "@/components/platform-admin/mfa-setup-dialog";
import { usePlatformAdminMfaDisable } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";

function DisableMfaDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const { refreshAdmin } = usePlatformAdminAuth();
  const [password, setPassword] = React.useState("");
  const disable = usePlatformAdminMfaDisable();

  const onOpenChangeReset = (next: boolean) => {
    onOpenChange(next);
    if (!next) {
      setPassword("");
      disable.reset();
    }
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await disable.mutateAsync(password);
    await refreshAdmin();
    onOpenChangeReset(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChangeReset}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Disable multi-factor authentication</DialogTitle>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={onSubmit}>
          <p className="text-sm text-muted-foreground">
            You&apos;ll lose access to the Danger Zone until MFA is set up again.
          </p>
          <Field label="Password" htmlFor="disable-mfa-password">
            <Input
              id="disable-mfa-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>
          {disable.isError && (
            <p className="text-sm font-medium text-danger">
              Couldn&apos;t disable MFA — check your password.
            </p>
          )}
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => onOpenChangeReset(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="danger" disabled={!password || disable.isPending}>
              {disable.isPending ? "Disabling…" : "Disable MFA"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function PlatformAdminSecurityPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading } = usePlatformAdminAuth();
  const [setupOpen, setSetupOpen] = React.useState(false);
  const [disableOpen, setDisableOpen] = React.useState(false);

  React.useEffect(() => {
    if (!authLoading && !admin) router.push("/platform-admin/login");
  }, [authLoading, admin, router]);

  if (authLoading || !admin) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-brand" />
            <CardTitle>Multi-factor authentication</CardTitle>
            <Badge variant={admin.mfa_enabled ? "success" : "outline"}>
              {admin.mfa_enabled ? "Enabled" : "Not set up"}
            </Badge>
          </div>
          <CardDescription>
            Required to access the Danger Zone. Uses a standard authenticator app (1Password,
            Authy, Google Authenticator).
          </CardDescription>
        </CardHeader>
        <CardContent>
          {admin.mfa_enabled ? (
            <Button type="button" variant="secondary" onClick={() => setDisableOpen(true)}>
              Disable MFA
            </Button>
          ) : (
            <Button type="button" onClick={() => setSetupOpen(true)}>
              Set up MFA
            </Button>
          )}
        </CardContent>
      </Card>

      <PlatformAdminMfaSetupDialog open={setupOpen} onOpenChange={setSetupOpen} />
      <DisableMfaDialog open={disableOpen} onOpenChange={setDisableOpen} />
    </div>
  );
}
