"use client";

import * as React from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { UserPlus } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { StepUpDialog } from "@/components/step-up-dialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { useInviteUser } from "@/lib/queries/team";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { useToast } from "@/lib/toast-context";
import type { RoleName } from "@/lib/types";

// Owner deliberately excluded -- the backend has always rejected direct-invite-as-Owner.
const ROLE_OPTIONS: { value: RoleName; label: string }[] = [
  { value: "Recruiter", label: "Recruiter" },
  { value: "Hiring Manager", label: "Hiring Manager" },
  { value: "Interviewer", label: "Interviewer" },
  { value: "TA Admin", label: "TA Admin" },
];

const schema = z.object({
  fullName: z.string().min(1, "Name is required"),
  email: z.string().email("Enter a valid email"),
});

type FormValues = z.infer<typeof schema>;

export function InviteTeammateDialog() {
  const [open, setOpen] = React.useState(false);
  const [role, setRole] = React.useState<RoleName>("Recruiter");
  const [pendingValues, setPendingValues] = React.useState<FormValues | null>(null);
  const [stepUpOpen, setStepUpOpen] = React.useState(false);
  const inviteUser = useInviteUser();
  const container = useThemeScopeContainer();
  const toast = useToast();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = (values: FormValues) => {
    setPendingValues(values);
    setStepUpOpen(true);
  };

  const handleVerified = async (stepUpToken: string) => {
    if (!pendingValues) return;
    await inviteUser.mutateAsync({
      input: { email: pendingValues.email, full_name: pendingValues.fullName, role },
      stepUpToken,
    });
    reset();
    setRole("Recruiter");
    setPendingValues(null);
    setOpen(false);
    toast({
      title: "Invite sent",
      description: `${pendingValues.email} will get an email shortly.`,
      variant: "success",
    });
  };

  return (
    <>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button size="sm">
            <UserPlus className="h-3.5 w-3.5" />
            Invite teammate
          </Button>
        </DialogTrigger>
        <DialogContent container={container}>
          <DialogHeader>
            <DialogTitle>Invite a teammate</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <Field label="Full name" htmlFor="fullName" error={errors.fullName?.message}>
              <Input id="fullName" {...register("fullName")} />
            </Field>
            <Field label="Email" htmlFor="email" error={errors.email?.message}>
              <Input id="email" type="email" {...register("email")} />
            </Field>
            <Field label="Role">
              <PillToggleGroup options={ROLE_OPTIONS} value={role} onChange={setRole} />
            </Field>
            {inviteUser.isError && (
              <p className="text-sm font-medium text-danger">
                Couldn&apos;t send the invite. Check the email and try again.
              </p>
            )}
            <DialogFooter>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setOpen(false)}
                disabled={inviteUser.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={inviteUser.isPending}>
                {inviteUser.isPending ? "Sending…" : "Send invite"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
      <StepUpDialog
        open={stepUpOpen}
        onOpenChange={setStepUpOpen}
        title="Confirm it's you"
        description="Inviting a teammate is a high-risk action — re-enter your password to continue."
        onVerified={handleVerified}
        container={container}
      />
    </>
  );
}
