"use client";

import * as React from "react";
import { QRCodeSVG } from "qrcode.react";
import { Check, Copy, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { usePlatformAdminMfaEnable, usePlatformAdminMfaSetup } from "@/lib/queries/platform-admin";

type Step = "loading" | "verify" | "backup-codes";

function CopyableSecret({ value }: { value: string }) {
  const [copied, setCopied] = React.useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div className="flex items-center gap-2 rounded-xl border border-border bg-secondary px-3.5 py-2.5">
      <code className="flex-1 break-all text-xs font-medium tracking-wide text-foreground">
        {value}
      </code>
      <button
        type="button"
        onClick={handleCopy}
        className="shrink-0 rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-white hover:text-foreground"
        aria-label="Copy"
      >
        {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
      </button>
    </div>
  );
}

export function PlatformAdminMfaSetupDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { refreshAdmin } = usePlatformAdminAuth();
  const setup = usePlatformAdminMfaSetup();
  const enable = usePlatformAdminMfaEnable();
  const [step, setStep] = React.useState<Step>("loading");
  const [code, setCode] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [backupCodes, setBackupCodes] = React.useState<string[]>([]);

  React.useEffect(() => {
    if (open) {
      setStep("loading");
      setCode("");
      setError(null);
      setup.mutate(undefined, { onSuccess: () => setStep("verify") });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!setup.data) return;
    setError(null);
    try {
      const res = await enable.mutateAsync({ secret: setup.data.secret, code });
      setBackupCodes(res.backup_codes);
      setStep("backup-codes");
      await refreshAdmin();
    } catch {
      setError("That code didn't match. Check your authenticator app and try again.");
    }
  };

  const handleDone = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={(next) => step !== "backup-codes" && onOpenChange(next)}>
      <DialogContent>
        {step === "loading" && (
          <div className="flex justify-center py-10 text-sm text-muted-foreground">
            Setting up…
          </div>
        )}

        {step === "verify" && setup.data && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-brand" />
                Set up multi-factor authentication
              </DialogTitle>
              <DialogDescription>
                Scan this with an authenticator app (1Password, Authy, Google Authenticator),
                then enter the 6-digit code it generates to confirm. Required before the Danger
                Zone becomes reachable.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleVerify} className="flex flex-col gap-4">
              <div className="flex justify-center rounded-xl border border-border bg-white p-4">
                <QRCodeSVG value={setup.data.provisioning_uri} size={176} />
              </div>
              <Field label="Can't scan it? Enter this key manually">
                <CopyableSecret value={setup.data.secret} />
              </Field>
              <Field label="6-digit code" htmlFor="platform-admin-mfa-verify-code">
                <Input
                  id="platform-admin-mfa-verify-code"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  placeholder="123456"
                  autoFocus
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                />
              </Field>
              {error && <p className="text-sm font-medium text-danger">{error}</p>}
              <DialogFooter>
                <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={code.length < 6 || enable.isPending}>
                  {enable.isPending ? "Confirming…" : "Confirm and enable"}
                </Button>
              </DialogFooter>
            </form>
          </>
        )}

        {step === "backup-codes" && (
          <>
            <DialogHeader>
              <DialogTitle>Save your backup codes</DialogTitle>
              <DialogDescription>
                Each code works once and gets you back in if you lose access to your
                authenticator app. They&apos;re shown only this one time — save them somewhere
                safe now.
              </DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-2 rounded-xl border border-border bg-secondary p-4">
              {backupCodes.map((c) => (
                <code key={c} className="text-sm font-medium tracking-wide text-foreground">
                  {c}
                </code>
              ))}
            </div>
            <DialogFooter>
              <Button type="button" onClick={handleDone}>
                I&apos;ve saved these codes
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
