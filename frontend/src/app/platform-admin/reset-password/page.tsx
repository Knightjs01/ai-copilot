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
import { platformAdminApiClient } from "@/lib/platform-admin-api-client";
import { ApiError } from "@/lib/api-client";

const schema = z
  .object({
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type FormValues = z.infer<typeof schema>;

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [formError, setFormError] = React.useState<string | null>(null);
  const [done, setDone] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    if (!token) return;
    setFormError(null);
    try {
      await platformAdminApiClient.post<void>("/platform-admin/password-reset/confirm", {
        reset_token: token,
        new_password: values.password,
      });
      setDone(true);
    } catch (err) {
      setFormError(
        err instanceof ApiError ? err.message : "Couldn't reset your password. Try again."
      );
    }
  };

  if (!token) {
    return (
      <p className="text-sm text-danger">
        This reset link is missing its token. Ask for a new one.
      </p>
    );
  }

  if (done) {
    return (
      <div className="flex flex-col gap-4">
        <p className="text-sm text-foreground">
          Your password has been reset. Every existing session has been signed out.
        </p>
        <Button
          type="button"
          size="lg"
          className="w-full"
          onClick={() => router.push("/platform-admin/login")}
        >
          Sign in
        </Button>
      </div>
    );
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
      <Field label="New password" htmlFor="password" error={errors.password?.message}>
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          {...register("password")}
        />
      </Field>
      <Field
        label="Confirm password"
        htmlFor="confirmPassword"
        error={errors.confirmPassword?.message}
      >
        <Input
          id="confirmPassword"
          type="password"
          autoComplete="new-password"
          {...register("confirmPassword")}
        />
      </Field>
      {formError && <p className="text-sm font-medium text-danger">{formError}</p>}
      <Button type="submit" size="lg" className="mt-2 w-full" disabled={isSubmitting}>
        {isSubmitting ? "Resetting…" : "Reset password"}
      </Button>
    </form>
  );
}

export default function PlatformAdminResetPasswordPage() {
  return (
    <AuthShell
      title="Reset your password"
      subtitle="Set a new password for your Phantom Command account."
      footer={null}
    >
      <React.Suspense
        fallback={
          <div className="flex justify-center py-4">
            <Spinner className="h-5 w-5 text-muted-foreground" />
          </div>
        }
      >
        <ResetPasswordForm />
      </React.Suspense>
    </AuthShell>
  );
}
