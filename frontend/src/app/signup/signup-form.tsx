"use client";

import * as React from "react";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AuthShell } from "@/components/auth-shell";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-context";

const schema = z.object({
  companyName: z.string().min(1, "Company name is required"),
  fullName: z.string().min(1, "Your name is required"),
  jobTitle: z.string().optional(),
  workEmail: z.string().email("Enter a valid work email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type FormValues = z.infer<typeof schema>;

export function SignupForm() {
  const { requestCompanyAccess } = useAuth();
  const [formError, setFormError] = React.useState<string | null>(null);
  const [submitted, setSubmitted] = React.useState<{ name: string; company: string; email: string } | null>(
    null
  );

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setFormError(null);
    try {
      await requestCompanyAccess({
        companyName: values.companyName,
        fullName: values.fullName,
        jobTitle: values.jobTitle,
        workEmail: values.workEmail,
        password: values.password,
      });
      setSubmitted({ name: values.fullName, company: values.companyName, email: values.workEmail });
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Couldn't submit your request.");
    }
  };

  if (submitted) {
    return (
      <AuthShell
        title="Request received"
        subtitle="Phantom verifies every organisation before granting access."
        footer={
          <>
            Already have a workspace?{" "}
            <Link
              href="/login/recruiter"
              className="font-medium text-foreground underline underline-offset-4"
            >
              Sign in
            </Link>
          </>
        }
      >
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <CheckCircle2 className="h-8 w-8 text-success" />
          <p className="text-sm text-foreground">
            Thanks, {submitted.name}. We&apos;re verifying {submitted.company}.
          </p>
          <p className="text-sm text-muted-foreground">
            You&apos;ll get an email at {submitted.email} once your workspace is ready.
          </p>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Request access"
      subtitle="Phantom is a verified professional hiring network — every employer workspace is reviewed before it goes live."
      footer={
        <>
          Already have a workspace?{" "}
          <Link
            href="/login/recruiter"
            className="font-medium text-foreground underline underline-offset-4"
          >
            Sign in
          </Link>
        </>
      }
    >
      <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
        <Field label="Company name" htmlFor="companyName" error={errors.companyName?.message}>
          <Input id="companyName" autoComplete="organization" {...register("companyName")} />
        </Field>
        <Field label="Your full name" htmlFor="fullName" error={errors.fullName?.message}>
          <Input id="fullName" autoComplete="name" {...register("fullName")} />
        </Field>
        <Field label="Job title (optional)" htmlFor="jobTitle" error={errors.jobTitle?.message}>
          <Input id="jobTitle" autoComplete="organization-title" {...register("jobTitle")} />
        </Field>
        <Field label="Work email" htmlFor="workEmail" error={errors.workEmail?.message}>
          <Input id="workEmail" type="email" autoComplete="email" {...register("workEmail")} />
        </Field>
        <Field label="Password" htmlFor="password" error={errors.password?.message}>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            {...register("password")}
          />
        </Field>
        {formError && <p className="text-sm font-medium text-danger">{formError}</p>}
        <Button type="submit" size="lg" className="mt-2 w-full" disabled={isSubmitting}>
          {isSubmitting ? "Submitting…" : "Request access"}
        </Button>
      </form>
    </AuthShell>
  );
}
