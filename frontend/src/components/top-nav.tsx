"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

import { PhantomIcon } from "@/components/phantom-icon";
import { useAuth } from "@/lib/auth-context";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? "") : "";
  return (first + last).toUpperCase();
}

export function TopNav() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-white/80 backdrop-blur">
      <div className="mx-auto grid h-16 max-w-6xl grid-cols-3 items-center px-6">
        <div className="flex items-center gap-6 justify-self-start">
          <Link href="/" aria-label="Phantom Hire home">
            <PhantomIcon className="h-9" priority />
          </Link>
          {user && (
            <nav className="flex items-center gap-4">
              <Link
                href="/projects"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Projects
              </Link>
              <Link
                href="/team"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Team
              </Link>
            </nav>
          )}
        </div>

        <Link href="/" aria-label="Phantom Hire home" className="justify-self-center">
          <Image
            src="/phantom-wordmark.png"
            alt="Phantom Hire"
            width={830}
            height={219}
            className="h-9 w-auto"
            priority
          />
        </Link>

        {user && (
          <div className="flex items-center gap-4 justify-self-end">
            <span className="text-sm text-muted-foreground">{user.full_name}</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
              {initials(user.full_name)}
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
        )}
      </div>
    </header>
  );
}
