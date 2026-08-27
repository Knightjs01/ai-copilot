"use client";

import * as React from "react";

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
import { requestPlatformAdminStepUpToken } from "@/lib/platform-admin-step-up";

interface PlatformAdminStepUpDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  onVerified: (token: string) => void | Promise<void>;
}

/** Re-authentication prompt for Danger Zone — mirrors components/step-up-dialog.tsx exactly,
 * against the platform-admin principal. Since MFA is mandatory (not just offered) for this path,
 * the authenticator-code field is always shown, never conditional on admin.mfa_enabled — a
 * caller only renders this once admin.mfa_enabled is already known true (see danger-zone/page.tsx). */
export function PlatformAdminStepUpDialog({
  open,
  onOpenChange,
  title = "Confirm it's you",
  description,
  onVerified,
}: PlatformAdminStepUpDialogProps) {
  const [password, setPassword] = React.useState("");
  const [mfaCode, setMfaCode] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  React.useEffect(() => {
    if (!open) {
      setPassword("");
      setMfaCode("");
      setError(null);
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const token = await requestPlatformAdminStepUpToken(password, mfaCode);
      // Deliberately not calling onOpenChange(false) here -- the caller is expected to stop
      // rendering this dialog once onVerified fires (see danger-zone/page.tsx, which swaps to
      // its real-content branch the moment a token exists). Closing it ourselves first would be
      // indistinguishable from the user cancelling, since both go through the same callback.
      await onVerified(token);
    } catch {
      setError("Couldn't verify. Check your password and authenticator code.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            {description ?? "This is a high-risk action — re-enter your password and authenticator code to continue."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Field label="Password" htmlFor="platform-admin-step-up-password">
            <Input
              id="platform-admin-step-up-password"
              type="password"
              autoComplete="current-password"
              autoFocus
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>
          <Field label="Authenticator code" htmlFor="platform-admin-step-up-mfa">
            <Input
              id="platform-admin-step-up-mfa"
              inputMode="numeric"
              autoComplete="one-time-code"
              placeholder="123456"
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value)}
            />
          </Field>
          {error && <p className="text-sm font-medium text-danger">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!password || !mfaCode || isSubmitting}>
              {isSubmitting ? "Verifying…" : "Confirm"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
