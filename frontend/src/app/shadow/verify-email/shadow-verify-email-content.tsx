"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle2, XCircle } from "lucide-react";

import { ShadowAuthShell } from "@/components/shadow/shadow-auth-shell";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { candidateApiClient } from "@/lib/candidate-api-client";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import type { CandidateMeResponse } from "@/lib/types";

type VerifyState = "verifying" | "success" | "error" | "no-token";

function ResendForm() {
  const { candidate } = useCandidateAuth();
  const [email, setEmail] = React.useState(candidate?.email ?? "");
  const [sent, setSent] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);
    try {
      await candidateApiClient.post("/candidate-auth/resend-verification", { email });
      setSent(true);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Couldn't send that. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (sent) {
    return (
      <p className="text-sm text-muted-foreground">
        If an account exists for that address, a new verification link is on its way.
      </p>
    );
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={onSubmit}>
      <Field label="Email" htmlFor="resend-email">
        <Input
          id="resend-email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </Field>
      {formError && <p className="text-sm font-medium text-danger">{formError}</p>}
      <Button type="submit" variant="brand" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? "Sending…" : "Resend verification email"}
      </Button>
    </form>
  );
}

// For a candidate who already verified via a link opened elsewhere (another tab/device) and is
// still sitting on this page -- re-checks the real, current status server-side before navigating,
// rather than trusting stale client state or just linking straight to Shadow.
function VerifiedContinueButton() {
  const router = useRouter();
  const { refreshCandidate } = useCandidateAuth();
  const [checking, setChecking] = React.useState(false);
  const [checkError, setCheckError] = React.useState<string | null>(null);

  const onClick = async () => {
    setChecking(true);
    setCheckError(null);
    try {
      const me = await candidateApiClient.get<CandidateMeResponse>("/candidate-auth/me");
      if (me.is_email_verified) {
        // ShadowAppShell gates /shadow/home on its own cached candidate.is_email_verified --
        // refresh that shared context too, or it'll immediately bounce back here on the stale
        // value.
        await refreshCandidate();
        router.push("/shadow/home");
      } else {
        setCheckError(
          "Your email hasn't been verified yet. Check your inbox for the link, or request a new one above."
        );
      }
    } catch {
      setCheckError("Couldn't check your verification status. Try again.");
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <Button type="button" variant="secondary" className="w-full" onClick={onClick} disabled={checking}>
        {checking ? "Checking…" : "Email Verified - Take me to Shadow"}
      </Button>
      {checkError && <p className="text-sm font-medium text-danger">{checkError}</p>}
    </div>
  );
}

function VerifyEmailBody() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [state, setState] = React.useState<VerifyState>(token ? "verifying" : "no-token");

  React.useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        await candidateApiClient.post("/candidate-auth/verify-email", { token });
        setState("success");
      } catch {
        setState("error");
      }
    })();
  }, [token]);

  if (state === "verifying") {
    return (
      <div className="flex flex-col items-center gap-3 py-4">
        <Spinner className="h-6 w-6 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">Confirming your email address…</p>
      </div>
    );
  }

  if (state === "success") {
    return (
      <div className="flex flex-col items-center gap-4 text-center">
        <CheckCircle2 className="h-8 w-8 text-success" />
        <p className="text-sm text-muted-foreground">
          Your email address is confirmed. You can now browse and apply on Shadow.
        </p>
        <Button asChild variant="brand" size="lg" className="w-full">
          <Link href="/shadow/home">Take me to Shadow</Link>
        </Button>
      </div>
    );
  }

  if (state === "error") {
    return (
      <div className="flex flex-col gap-5">
        <div className="flex flex-col items-center gap-3 text-center">
          <XCircle className="h-8 w-8 text-danger" />
          <p className="text-sm text-muted-foreground">
            This link has expired or has already been used. Request a new one below.
          </p>
        </div>
        <ResendForm />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-muted-foreground">
        Confirm your email address to browse and apply on Shadow. Enter your email to get a
        verification link.
      </p>
      <ResendForm />
      <VerifiedContinueButton />
    </div>
  );
}

export function ShadowVerifyEmailContent() {
  return (
    <ShadowAuthShell title="Verify your email" subtitle="One more step before you can use Shadow." footer={null}>
      <React.Suspense
        fallback={
          <div className="flex justify-center py-4">
            <Spinner className="h-5 w-5 text-muted-foreground" />
          </div>
        }
      >
        <VerifyEmailBody />
      </React.Suspense>
    </ShadowAuthShell>
  );
}
