"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AuthShell } from "@/components/auth-shell";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";

const schema = z.object({
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type FormValues = z.infer<typeof schema>;

function AcceptInviteForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const { acceptInvite } = useAuth();
  const [formError, setFormError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    if (!token) return;
    setFormError(null);
    try {
      await acceptInvite(token, values.password);
      router.push("/projects");
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Couldn't accept this invite.");
    }
  };

  if (!token) {
    return (
      <p className="text-sm text-danger">
        This invite link is missing its token — ask whoever invited you to resend it.
      </p>
    );
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
      <Field label="Set a password" htmlFor="password" error={errors.password?.message}>
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          {...register("password")}
        />
      </Field>
      {formError && <p className="text-sm font-medium text-danger">{formError}</p>}
      <Button type="submit" size="lg" className="mt-2 w-full" disabled={isSubmitting}>
        {isSubmitting ? "Joining…" : "Accept invite"}
      </Button>
    </form>
  );
}

export default function AcceptInvitePage() {
  return (
    <AuthShell
      title="You're invited"
      subtitle="Set a password to join your team's workspace."
      footer={null}
    >
      <React.Suspense
        fallback={
          <div className="flex justify-center py-4">
            <Spinner className="h-5 w-5 text-muted-foreground" />
          </div>
        }
      >
        <AcceptInviteForm />
      </React.Suspense>
    </AuthShell>
  );
}
