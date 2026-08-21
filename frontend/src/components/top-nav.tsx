"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut, Moon, Search, Sun } from "lucide-react";
import Image from "next/image";

import { useCommandPalette } from "@/components/command-palette/command-palette-provider";
import { Avatar } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/lib/theme-context";

export function TopNav({ container }: { container?: HTMLElement | null }) {
  const { user, logout, hasPermission } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { openPalette } = useCommandPalette();
  const router = useRouter();
  const canViewHistoricVault = hasPermission("historic_vault.view");
  const canViewShadowJobs = hasPermission("shadow_jobs.view");
  const canSearchCandidates = hasPermission("shadow_candidates.search");
  const canManageCompany = hasPermission("company.manage_settings");
  const canViewPipeline = hasPermission("candidates.view");

  const handleLogout = async () => {
    await logout();
    router.push("/login/recruiter");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto grid h-16 max-w-6xl grid-cols-3 items-center px-6">
        <div className="flex items-center gap-6 justify-self-start">
          <Link href="/home" aria-label="Phantom ATS home">
            <Image
              src="/phantom-ats-wordmark.png"
              alt="Phantom ATS"
              width={1388}
              height={339}
              className="h-8 w-auto"
              priority
            />
          </Link>
          {user && (
            <nav className="flex items-center gap-4">
              <Link
                href="/home"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Home
              </Link>
              <Link
                href="/projects"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Roles
              </Link>
              {canViewPipeline && (
                <Link
                  href="/pipeline"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Pipeline
                </Link>
              )}
              <Link
                href="/team"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Team
              </Link>
              {canViewShadowJobs && (
                <Link
                  href="/shadow-jobs"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Shadow Jobs
                </Link>
              )}
              {canViewHistoricVault && (
                <Link
                  href="/historic-vault"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Historic Vault
                </Link>
              )}
              {canSearchCandidates && (
                <Link
                  href="/search-candidates"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Search Candidates
                </Link>
              )}
              {canManageCompany && (
                <Link
                  href="/company"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Company Profile
                </Link>
              )}
              <Link
                href="/security"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Security
              </Link>
            </nav>
          )}
        </div>

        <div aria-hidden />

        {user && (
          <div className="flex items-center gap-2 justify-self-end">
            <button
              type="button"
              onClick={openPalette}
              className="flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              <Search className="h-3.5 w-3.5" />
              Search…
              <kbd className="rounded border border-border bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                ⌘K
              </kbd>
            </button>

            <button
              type="button"
              onClick={toggleTheme}
              aria-label="Toggle dark mode"
              className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button type="button" aria-label="Account menu">
                  <Avatar name={user.full_name} />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent container={container} align="end">
                <DropdownMenuLabel>{user.full_name}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onSelect={handleLogout}>
                  <LogOut className="h-3.5 w-3.5" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>
    </header>
  );
}
