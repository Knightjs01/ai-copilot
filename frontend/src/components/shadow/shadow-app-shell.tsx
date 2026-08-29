"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { ShadowAppHeader } from "@/components/shadow/shadow-app-header";
import { ShadowSidebar } from "@/components/shadow/shadow-sidebar";
import { Spinner } from "@/components/ui/spinner";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { cn } from "@/lib/utils";

// The single auth-conditional shell decision point for Shadow. Covers both the public board
// (candidate optional -- logged-out visitors get today's lightweight header, no sidebar, matching
// how the ATS has no anonymous-access story at all to design around) and the (candidate)-only
// route group (requireAuth redirects to /shadow/login, absorbing what that layout used to do
// itself).
export function ShadowAppShell({
  children,
  requireAuth = false,
  mainClassName,
  chromeless = false,
}: {
  children: React.ReactNode;
  requireAuth?: boolean;
  mainClassName?: string;
  // No sidebar/header nav -- used by the Passport build wizard so it feels like a contained
  // walkthrough rather than a page inside the wider Shadow app. Still requires auth exactly like
  // the normal candidate shell; only the chrome around the content changes.
  chromeless?: boolean;
}) {
  const { candidate, isLoading } = useCandidateAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  React.useEffect(() => {
    if (requireAuth && !isLoading && !candidate) {
      router.replace("/shadow/login");
    }
  }, [requireAuth, isLoading, candidate, router]);

  // A logged-in candidate must confirm their email before using ANY of the authenticated Shadow
  // experience -- including the public board itself (requireAuth=false pages like /shadow),
  // not just the requireAuth-only routes. Deliberately NOT gated on requireAuth: an anonymous,
  // logged-out visitor still gets today's lightweight board (candidate is null, so this never
  // fires for them) -- only a signed-in-but-unverified candidate is redirected away. Exceptions:
  // the Passport wizard itself (they haven't finished building it yet) and this page's own
  // destination (or they could never get there). No grace period, matching
  // require_verified_candidate on the backend -- verification is only ever asked for after the
  // wizard is already done.
  React.useEffect(() => {
    if (
      candidate &&
      !candidate.is_email_verified &&
      pathname !== "/shadow/passport" &&
      pathname !== "/shadow/verify-email"
    ) {
      router.replace("/shadow/verify-email");
    }
  }, [candidate, pathname, router]);

  const pendingVerificationRedirect =
    !!candidate &&
    !candidate.is_email_verified &&
    pathname !== "/shadow/passport" &&
    pathname !== "/shadow/verify-email";

  if ((requireAuth && (isLoading || !candidate)) || pendingVerificationRedirect) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  if (candidate && chromeless) {
    return (
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
          <div className="mx-auto flex h-16 max-w-4xl items-center px-6">
            <Link href="/shadow" aria-label="Shadow home">
              <Image
                src="/phantom-shadow-logo-new.png"
                alt="Phantom Shadow"
                width={2172}
                height={724}
                className="h-9 w-auto"
                priority
              />
            </Link>
          </div>
        </header>
        <main className={cn("mx-auto w-full px-6 py-10", mainClassName ?? "max-w-4xl")}>
          {children}
        </main>
      </div>
    );
  }

  if (candidate) {
    return (
      <div className="flex min-h-screen">
        <ShadowSidebar mobileOpen={mobileOpen} onMobileOpenChange={setMobileOpen} />
        <div className="flex min-w-0 flex-1 flex-col">
          <ShadowAppHeader onOpenMobileNav={() => setMobileOpen(true)} />
          <main className={cn("mx-auto w-full flex-1 px-6 py-10", mainClassName ?? "max-w-4xl")}>
            {children}
          </main>
        </div>
      </div>
    );
  }

  // Anonymous: the logged-out half of the old ShadowTopNav, ported in verbatim -- logo + Log
  // in/Get started, no sidebar. isLoading is treated as "not authed" here so anonymous visitors
  // never block on a candidate-auth check; a candidate who IS logged in will see this for one
  // frame before useCandidateAuth() resolves and the sidebar shell above takes over.
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link href="/shadow" aria-label="Shadow home">
            <Image
              src="/phantom-shadow-logo-new.png"
              alt="Phantom Shadow"
              width={2172}
              height={724}
              className="h-9 w-auto"
              priority
            />
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/shadow/login" className="text-sm text-muted-foreground hover:text-foreground">
              Log in
            </Link>
            <Link
              href="/shadow/signup"
              className="rounded-full bg-brand px-4 py-2 text-sm font-medium text-brand-foreground hover:bg-brand/90"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>
      <main className={cn("mx-auto px-6 py-10", mainClassName ?? "max-w-4xl")}>{children}</main>
    </div>
  );
}
