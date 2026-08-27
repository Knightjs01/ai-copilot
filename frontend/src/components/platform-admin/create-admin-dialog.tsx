"use client";

import * as React from "react";

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
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { useCreateAdmin } from "@/lib/queries/platform-admin";
import { PLATFORM_ADMIN_ROLE_LABEL } from "@/lib/status-display";
import type { PlatformAdminRoleName } from "@/lib/types";

const ROLE_OPTIONS: { value: PlatformAdminRoleName; label: string }[] = (
  Object.keys(PLATFORM_ADMIN_ROLE_LABEL) as PlatformAdminRoleName[]
).map((value) => ({ value, label: PLATFORM_ADMIN_ROLE_LABEL[value] }));

export function CreateAdminDialog() {
  const [open, setOpen] = React.useState(false);
  const [fullName, setFullName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [role, setRole] = React.useState<PlatformAdminRoleName>("Reviewer");
  const createAdmin = useCreateAdmin();

  const onOpenChange = (next: boolean) => {
    setOpen(next);
    if (!next) {
      setFullName("");
      setEmail("");
      setPassword("");
      setRole("Reviewer");
      createAdmin.reset();
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createAdmin.mutate(
      { fullName, email, password, role },
      { onSuccess: () => onOpenChange(false) }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm">Create admin</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create a platform admin</DialogTitle>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={onSubmit}>
          <Field label="Full name" htmlFor="admin-full-name">
            <Input
              id="admin-full-name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </Field>
          <Field label="Email" htmlFor="admin-email">
            <Input
              id="admin-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </Field>
          <Field label="Initial password" htmlFor="admin-password">
            <Input
              id="admin-password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
          </Field>
          <Field label="Role">
            <PillToggleGroup options={ROLE_OPTIONS} value={role} onChange={setRole} />
          </Field>
          {createAdmin.isError && (
            <p className="text-sm font-medium text-danger">
              Couldn&apos;t create that admin — check the email isn&apos;t already in use.
            </p>
          )}
          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => onOpenChange(false)}
              disabled={createAdmin.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createAdmin.isPending}>
              {createAdmin.isPending ? "Creating…" : "Create admin"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
