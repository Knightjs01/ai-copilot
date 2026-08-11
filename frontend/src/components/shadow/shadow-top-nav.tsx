"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

import { useCandidateAuth } from "@/lib/candidate-auth-context";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? "") : "";
  return (first + last).toUpperCase();
}

export function ShadowTopNav() {
  const { candidate, logout } = useCandidateAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/shadow");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-white/80 backdrop-blur">
      <div className="mx-auto grid h-16 max-w-6xl grid-cols-3 items-center px-6">
        <div className="flex items-center gap-6 justify-self-start">
          <Link href="/shadow" aria-label="Shadow home">
            <Image
              src="/shadow-icon.png"
              alt=""
              width={557}
              height={550}
              className="h-10 w-auto"
              priority
            />
          </Link>
          <nav className="flex items-center gap-4">
            <Link
              href="/shadow"
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              Job board
            </Link>
            {candidate && (
              <>
                <Link
                  href="/shadow/passport"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Phantom Passport
                </Link>
                <Link
                  href="/shadow/applications"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Applications
                </Link>
              </>
            )}
          </nav>
        </div>

        <Link href="/shadow" aria-label="Shadow home" className="justify-self-center">
          <Image
            src="/shadow-wordmark.png"
            alt="Shadow: Anonymous Job Board"
            width={1629}
            height={1049}
            className="h-9 w-auto"
            priority
          />
        </Link>

        {candidate ? (
          <div className="flex items-center gap-4 justify-self-end">
            <span className="text-sm text-muted-foreground">{candidate.full_name}</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-xs font-semibold text-brand-foreground">
              {initials(candidate.full_name)}
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              aria-label="Log out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3 justify-self-end">
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
        )}
      </div>
    </header>
  );
}
