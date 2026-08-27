"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useChangePassword } from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";

export function ChangePasswordDialog() {
  const router = useRouter();
  const { logout } = usePlatformAdminAuth();
  const [open, setOpen] = React.useState(false);
  const [currentPassword, setCurrentPassword] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const changePassword = useChangePassword();

  const mismatch = confirmPassword.length > 0 && newPassword !== confirmPassword;
  const canSubmit =
    currentPassword.length > 0 && newPassword.length >= 8 && newPassword === confirmPassword;

  const onOpenChange = (next: boolean) => {
    setOpen(next);
    if (!next) {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      changePassword.reset();
    }
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    await changePassword.mutateAsync({ currentPassword, newPassword });
    // Changing the password revokes every session, including this one -- sign out locally and
    // send the admin back to log in with the new password rather than leave a stale UI state.
    await logout();
    router.push("/platform-admin/login");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button type="button" variant="secondary" size="sm">
          Change password
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Change password</DialogTitle>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={onSubmit}>
          <Field label="Current password" htmlFor="current-password">
            <Input
              id="current-password"
              type="password"
              autoComplete="current-password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
          </Field>
          <Field label="New password" htmlFor="new-password">
            <Input
              id="new-password"
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              minLength={8}
            />
          </Field>
          <Field
            label="Confirm new password"
            htmlFor="confirm-password"
            error={mismatch ? "Passwords don't match" : undefined}
          >
            <Input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </Field>
          {changePassword.isError && (
            <p className="text-sm font-medium text-danger">
              Couldn&apos;t change your password — check your current password and try again.
            </p>
          )}
          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => onOpenChange(false)}
              disabled={changePassword.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!canSubmit || changePassword.isPending}>
              {changePassword.isPending ? "Changing…" : "Change password"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
