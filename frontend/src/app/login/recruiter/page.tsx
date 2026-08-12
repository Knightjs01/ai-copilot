"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AuthShell } from "@/components/auth-shell";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-context";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormValues = z.infer<typeof schema>;

export default function RecruiterLoginPage() {
  const router = useRouter();
  const { login, verifyMfa } = useAuth();
  const [formError, setFormError] = React.useState<string | null>(null);
  const [challengeToken, setChallengeToken] = React.useState<string | null>(null);
  const [mfaCode, setMfaCode] = React.useState("");
  const [isVerifyingMfa, setIsVerifyingMfa] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setFormError(null);
    try {
      const result = await login(values.email, values.password);
      if (result.mfaRequired) {
        setChallengeToken(result.challengeToken);
        return;
      }
      router.push("/projects");
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Couldn't sign in. Try again.");
    }
  };

  const handleVerifyMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!challengeToken) return;
    setFormError(null);
    setIsVerifyingMfa(true);
    try {
      await verifyMfa(challengeToken, mfaCode);
      router.push("/projects");
    } catch {
      setFormError("That code didn't match. Check your authenticator app and try again.");
    } finally {
      setIsVerifyingMfa(false);
    }
  };

  if (challengeToken) {
    return (
      <AuthShell
        title="Enter your code"
        subtitle="Enter the code from your authenticator app, or one of your backup codes."
        footer={
          <button
            type="button"
            onClick={() => setChallengeToken(null)}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            ← Back to sign in
          </button>
        }
      >
        <form className="flex flex-col gap-4" onSubmit={handleVerifyMfa}>
          <Field label="Authentication code" htmlFor="mfa-code">
            <Input
              id="mfa-code"
              inputMode="text"
              autoComplete="one-time-code"
              autoFocus
              placeholder="123456"
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value)}
            />
          </Field>
          {formError && <p className="text-sm font-medium text-danger">{formError}</p>}
          <Button
            type="submit"
            size="lg"
            className="mt-2 w-full"
            disabled={isVerifyingMfa || mfaCode.length < 6}
          >
            {isVerifyingMfa ? "Verifying…" : "Verify and sign in"}
          </Button>
        </form>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to your Talent Acquisition workspace."
      footer={
        <div className="flex flex-col items-center gap-2">
          <span>
            Don&apos;t have a workspace yet?{" "}
            <Link href="/signup" className="font-medium text-foreground underline underline-offset-4">
              Create one
            </Link>
          </span>
          <Link href="/login" className="text-xs text-muted-foreground hover:text-foreground">
            ← Not a recruiter? Choose a different login
          </Link>
        </div>
      }
    >
      <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
        <Field label="Email" htmlFor="email" error={errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" {...register("email")} />
        </Field>
        <Field label="Password" htmlFor="password" error={errors.password?.message}>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            {...register("password")}
          />
        </Field>
        {formError && <p className="text-sm font-medium text-danger">{formError}</p>}
        <Button type="submit" size="lg" className="mt-2 w-full" disabled={isSubmitting}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthShell>
  );
}
