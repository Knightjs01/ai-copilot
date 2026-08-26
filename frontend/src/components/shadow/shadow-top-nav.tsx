"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut, Search } from "lucide-react";

import { useShadowCommandPalette } from "@/components/shadow/shadow-command-palette-provider";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useMyMessageThreads } from "@/lib/queries/messages";

function initials(firstName: string, lastName: string | null): string {
  return ((firstName[0] ?? "") + (lastName?.[0] ?? "")).toUpperCase();
}

export function ShadowTopNav() {
  const { candidate, logout } = useCandidateAuth();
  const router = useRouter();
  const { openPalette } = useShadowCommandPalette();
  const { data: threads } = useMyMessageThreads({ enabled: !!candidate });
  const unreadCount = threads?.reduce((sum, t) => sum + t.unread_count, 0) ?? 0;

  const handleLogout = async () => {
    await logout();
    router.push("/shadow");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-white/80 backdrop-blur">
      <div className="mx-auto grid h-24 max-w-6xl grid-cols-3 items-center px-6">
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
          <nav className="hidden items-center gap-4 md:flex">
            {candidate && (
              <Link
                href="/shadow/home"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Home
              </Link>
            )}
            <Link
              href="/shadow"
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              Discover
            </Link>
            {candidate && (
              <>
                <Link
                  href="/shadow/for-you"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  For You
                </Link>
                <Link
                  href="/shadow/applications"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Applications
                </Link>
                <Link
                  href="/shadow/messages"
                  className="flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Messages
                  {unreadCount > 0 && (
                    <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-info px-1 text-[10px] font-semibold text-info-foreground">
                      {unreadCount}
                    </span>
                  )}
                </Link>
                <Link
                  href="/shadow/interviews"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Interviews
                </Link>
                <Link
                  href="/shadow/passport"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  My Passport
                </Link>
                <Link
                  href="/shadow/saved-jobs"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Saved Jobs
                </Link>
              </>
            )}
          </nav>
        </div>

        <Link href="/shadow" aria-label="Shadow home" className="justify-self-center">
          <Image
            src="/phantom-shadow-logo-new.png"
            alt="Phantom Shadow: Anonymous Job Board"
            width={2172}
            height={724}
            className="h-12 w-auto"
            priority
          />
        </Link>

        {candidate ? (
          <div className="flex items-center gap-3 justify-self-end">
            <button
              type="button"
              onClick={openPalette}
              className="hidden items-center gap-2 rounded-full border border-border bg-white px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground sm:flex"
            >
              <Search className="h-3.5 w-3.5" />
              Search
              <kbd className="rounded border border-border bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                ⌘K
              </kbd>
            </button>
            <span className="hidden text-sm text-muted-foreground lg:inline">
              {candidate.first_name} {candidate.last_name}
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-xs font-semibold text-brand-foreground">
              {initials(candidate.first_name, candidate.last_name)}
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
