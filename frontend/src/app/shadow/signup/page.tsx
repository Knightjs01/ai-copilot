"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ShadowAuthShell } from "@/components/shadow/shadow-auth-shell";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useCandidateAuth } from "@/lib/candidate-auth-context";

const schema = z.object({
  fullName: z.string().min(1, "Your name is required"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type FormValues = z.infer<typeof schema>;

export default function ShadowSignupPage() {
  const router = useRouter();
  const { signup } = useCandidateAuth();
  const [formError, setFormError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setFormError(null);
    try {
      await signup(values.email, values.password, values.fullName);
      router.push("/shadow/passport");
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Couldn't create your Passport.");
    }
  };

  return (
    <ShadowAuthShell
      title="Build your Phantom Passport"
      subtitle="One reusable profile, built once, applied anywhere. Stay pseudonymous until you choose to reveal who you are."
      footer={
        <>
          Already have a Passport?{" "}
          <Link
            href="/shadow/login"
            className="font-medium text-foreground underline underline-offset-4"
          >
            Sign in
          </Link>
        </>
      }
    >
      <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
        <Field label="Your full name" htmlFor="fullName" error={errors.fullName?.message}>
          <Input id="fullName" autoComplete="name" {...register("fullName")} />
        </Field>
        <Field label="Email" htmlFor="email" error={errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" {...register("email")} />
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
        <Button type="submit" variant="brand" size="lg" className="mt-2 w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating your Passport…" : "Create your Passport"}
        </Button>
      </form>
    </ShadowAuthShell>
  );
}
