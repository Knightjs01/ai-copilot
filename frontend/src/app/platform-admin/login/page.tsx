"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { QRCodeSVG } from "qrcode.react";
import { Check, Copy } from "lucide-react";

import { AuthShell } from "@/components/auth-shell";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import type { MfaSetupResponse } from "@/lib/types";

function CopyableSecret({ value }: { value: string }) {
  const [copied, setCopied] = React.useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div className="flex items-center gap-2 rounded-xl border border-border bg-secondary px-3.5 py-2.5">
      <code className="flex-1 break-all text-xs font-medium tracking-wide text-foreground">
        {value}
      </code>
      <button
        type="button"
        onClick={handleCopy}
        className="shrink-0 rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-white hover:text-foreground"
        aria-label="Copy"
      >
        {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
      </button>
    </div>
  );
}

// Phantom Command requires MFA at login with no opt-out. Three real states beyond the plain
// password screen: already enrolled (enter a code), never enrolled (walk through enrollment
// inline, right here, before a session exists at all), or -- after enrolling -- a one-time
// backup-codes reveal before landing in the portal. Mirrors recruiter-login-form.tsx's
// password->code branching and PlatformAdminMfaSetupDialog's enrollment body, combined into one
// page since there's no session yet to gate a dialog on.
type Screen =
  | { step: "password" }
  | { step: "mfa-code"; challengeToken: string }
  | { step: "enroll-loading"; pendingToken: string }
  | { step: "enroll-verify"; pendingToken: string; setup: MfaSetupResponse }
  | { step: "enroll-backup-codes"; backupCodes: string[] };

export default function PlatformAdminLoginPage() {
  const router = useRouter();
  const { login, verifyMfa, getPendingMfaSetup, enrollMfa } = usePlatformAdminAuth();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [code, setCode] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [screen, setScreen] = React.useState<Screen>({ step: "password" });

  React.useEffect(() => {
    if (screen.step !== "enroll-loading") return;
    const pendingToken = screen.pendingToken;
    getPendingMfaSetup(pendingToken)
      .then((setup) => setScreen({ step: "enroll-verify", pendingToken, setup }))
      .catch(() => {
        setError("Couldn't start MFA setup. Try signing in again.");
        setScreen({ step: "password" });
      });
  }, [screen, getPendingMfaSetup]);

  const onSubmitPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const result = await login(email, password);
      if (result.mfaRequired) {
        setScreen({ step: "mfa-code", challengeToken: result.challengeToken });
      } else if (result.mfaEnrollmentRequired) {
        setScreen({ step: "enroll-loading", pendingToken: result.pendingToken });
      } else {
        router.push("/platform-admin");
      }
    } catch {
      setError("Invalid email or password.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const onVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (screen.step !== "mfa-code") return;
    setError(null);
    setIsSubmitting(true);
    try {
      await verifyMfa(screen.challengeToken, code);
      router.push("/platform-admin");
    } catch {
      setError("That code didn't match. Check your authenticator app and try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const onConfirmEnroll = async (e: React.FormEvent) => {
    e.preventDefault();
    if (screen.step !== "enroll-verify") return;
    setError(null);
    setIsSubmitting(true);
    try {
      const res = await enrollMfa(screen.pendingToken, screen.setup.secret, code);
      setScreen({ step: "enroll-backup-codes", backupCodes: res.backup_codes });
    } catch {
      setError("That code didn't match. Check your authenticator app and try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const backToPassword = () => {
    setError(null);
    setCode("");
    setScreen({ step: "password" });
  };

  if (screen.step === "mfa-code") {
    return (
      <AuthShell
        title="Enter your code"
        subtitle="Enter the code from your authenticator app, or one of your backup codes."
        footer={
          <button
            type="button"
            onClick={backToPassword}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            ← Back to sign in
          </button>
        }
      >
        <form className="flex flex-col gap-4" onSubmit={onVerifyCode}>
          <Field label="Authentication code" htmlFor="mfa-code">
            <Input
              id="mfa-code"
              inputMode="text"
              autoComplete="one-time-code"
              autoFocus
              placeholder="123456"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
          </Field>
          {error && <p className="text-sm font-medium text-danger">{error}</p>}
          <Button type="submit" size="lg" className="mt-2 w-full" disabled={isSubmitting || code.length < 6}>
            {isSubmitting ? "Verifying…" : "Verify and sign in"}
          </Button>
        </form>
      </AuthShell>
    );
  }

  if (screen.step === "enroll-loading") {
    return (
      <AuthShell title="Setting up multi-factor authentication" subtitle="One moment…" footer={null}>
        <div className="flex justify-center py-10 text-sm text-muted-foreground">Setting up…</div>
      </AuthShell>
    );
  }

  if (screen.step === "enroll-verify") {
    return (
      <AuthShell
        title="Set up multi-factor authentication"
        subtitle="Required for every Phantom Command sign-in. Scan this with an authenticator app (1Password, Authy, Google Authenticator), then enter the 6-digit code it generates."
        footer={
          <button
            type="button"
            onClick={backToPassword}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            ← Back to sign in
          </button>
        }
      >
        <form className="flex flex-col gap-4" onSubmit={onConfirmEnroll}>
          <div className="flex justify-center rounded-xl border border-border bg-white p-4">
            <QRCodeSVG value={screen.setup.provisioning_uri} size={176} />
          </div>
          <Field label="Can't scan it? Enter this key manually">
            <CopyableSecret value={screen.setup.secret} />
          </Field>
          <Field label="6-digit code" htmlFor="enroll-code">
            <Input
              id="enroll-code"
              inputMode="numeric"
              autoComplete="one-time-code"
              placeholder="123456"
              autoFocus
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
          </Field>
          {error && <p className="text-sm font-medium text-danger">{error}</p>}
          <Button type="submit" size="lg" className="mt-2 w-full" disabled={isSubmitting || code.length < 6}>
            {isSubmitting ? "Confirming…" : "Confirm and enable"}
          </Button>
        </form>
      </AuthShell>
    );
  }

  if (screen.step === "enroll-backup-codes") {
    return (
      <AuthShell
        title="Save your backup codes"
        subtitle="Each code works once and gets you back in if you lose access to your authenticator app. They're shown only this one time — save them somewhere safe now."
        footer={null}
      >
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-2 rounded-xl border border-border bg-secondary p-4">
            {screen.backupCodes.map((c) => (
              <code key={c} className="text-sm font-medium tracking-wide text-foreground">
                {c}
              </code>
            ))}
          </div>
          <Button type="button" size="lg" className="w-full" onClick={() => router.push("/platform-admin")}>
            I&apos;ve saved these codes
          </Button>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Phantom Command"
      subtitle="Internal staff only."
      footer="Not a Phantom staff member? Close this tab."
    >
      <form className="flex flex-col gap-4" onSubmit={onSubmitPassword}>
        <Field label="Email" htmlFor="email">
          <Input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        <Field label="Password" htmlFor="password">
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        {error && <p className="text-sm font-medium text-danger">{error}</p>}
        <Button type="submit" size="lg" className="mt-2 w-full" disabled={isSubmitting}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthShell>
  );
}
