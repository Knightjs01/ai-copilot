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
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useCandidateMfaDisable } from "@/lib/queries/candidate-security";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";

// Mirrors components/security/mfa-disable-dialog.tsx (the company equivalent) exactly, swapped
// to candidate auth and /candidate-auth/mfa/disable.
export function CandidateMfaDisableDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { refreshCandidate } = useCandidateAuth();
  const disable = useCandidateMfaDisable();
  const container = useThemeScopeContainer();
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!open) {
      setPassword("");
      setError(null);
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await disable.mutateAsync(password);
      await refreshCandidate();
      onOpenChange(false);
    } catch {
      setError("Wrong password.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent container={container}>
        <DialogHeader>
          <DialogTitle>Disable multi-factor authentication</DialogTitle>
          <DialogDescription>
            This removes the extra login step and deletes your backup codes. Confirm with your
            password.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Field label="Password" htmlFor="candidate-mfa-disable-password">
            <Input
              id="candidate-mfa-disable-password"
              type="password"
              autoComplete="current-password"
              autoFocus
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>
          {error && <p className="text-sm font-medium text-danger">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
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
