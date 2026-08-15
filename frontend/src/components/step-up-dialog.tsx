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
import { useAuth } from "@/lib/auth-context";
import { requestStepUpToken } from "@/lib/step-up";

interface StepUpDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  onVerified: (token: string) => void | Promise<void>;
  // Optional Portal target so callers rendered inside a page-scoped dark theme (see
  // dialog.tsx's own comment) stay themed correctly — defaults to document.body when omitted,
  // so this is additive and every existing caller is unaffected.
  container?: HTMLElement | null;
}

/** Re-authentication prompt for high-risk actions (identity reveal, project purge, admin
 * invite) — a valid session isn't enough for these; the backend also requires proof the person
 * at the keyboard just re-supplied their password (and MFA code, if enrolled). Render this
 * alongside the action's own confirm dialog and call the mutation from onVerified. */
export function StepUpDialog({
  open,
  onOpenChange,
  title = "Confirm it's you",
  description,
  onVerified,
  container,
}: StepUpDialogProps) {
  const { user } = useAuth();
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
      const token = await requestStepUpToken(password, user?.mfa_enabled ? mfaCode : undefined);
      onOpenChange(false);
      await onVerified(token);
    } catch {
      setError(
        user?.mfa_enabled
          ? "Couldn't verify. Check your password and authenticator code."
          : "Couldn't verify. Check your password."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent container={container}>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            {description ?? "This is a high-risk action — re-enter your password to continue."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Field label="Password" htmlFor="step-up-password">
            <Input
              id="step-up-password"
              type="password"
              autoComplete="current-password"
              autoFocus
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>
          {user?.mfa_enabled && (
            <Field label="Authenticator code">
              <Input
                inputMode="numeric"
                autoComplete="one-time-code"
                placeholder="123456"
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
              />
            </Field>
          )}
          {error && <p className="text-sm font-medium text-danger">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!password || isSubmitting}>
              {isSubmitting ? "Verifying…" : "Confirm"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
