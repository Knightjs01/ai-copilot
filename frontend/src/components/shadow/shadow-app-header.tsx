"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { LogOut, Menu, Moon, Search, Sun } from "lucide-react";

import { useShadowCommandPalette } from "@/components/shadow/shadow-command-palette-provider";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useShadowTheme } from "@/lib/shadow-theme-context";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";

// Mirrors app-header.tsx's structure -- search/palette trigger, avatar dropdown, theme toggle --
// swapped to candidate auth and the Shadow command palette. No Breadcrumbs equivalent exists for
// Shadow, so that slot is simply omitted rather than inventing one. "Settings" links to
// /shadow/passport, the closest thing Shadow has to a candidate profile/settings surface today.
export function ShadowAppHeader({ onOpenMobileNav }: { onOpenMobileNav: () => void }) {
  const { theme, toggleTheme } = useShadowTheme();
  const { openPalette } = useShadowCommandPalette();
  const { candidate, logout } = useCandidateAuth();
  const router = useRouter();
  const container = useThemeScopeContainer();

  const handleLogout = async () => {
    await logout();
    router.push("/shadow");
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-4 border-b border-border bg-background/80 px-6 backdrop-blur">
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        aria-label="Open menu"
        onClick={onOpenMobileNav}
      >
        <Menu className="h-5 w-5" />
      </Button>

      <div className="hidden md:block" />

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={openPalette}
          className="hidden items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground sm:flex"
        >
          <Search className="h-3.5 w-3.5" />
          Search…
          <kbd className="rounded border border-border bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
            ⌘K
          </kbd>
        </button>

        {candidate && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                aria-label="Account menu"
                className="flex items-center gap-2 rounded-full px-2 py-1 text-left transition-colors hover:bg-secondary"
              >
                <Avatar
                  name={`${candidate.first_name} ${candidate.last_name ?? ""}`}
                  className="h-7 w-7 text-xs"
                />
                <span className="hidden max-w-[10rem] truncate text-sm font-medium text-foreground sm:inline">
                  {candidate.first_name} {candidate.last_name}
                </span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent container={container} align="end" side="bottom">
              <DropdownMenuLabel>
                {candidate.first_name} {candidate.last_name}
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={() => router.push("/shadow/passport")}>
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={handleLogout}>
                <LogOut className="h-3.5 w-3.5" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        <button
          type="button"
          onClick={toggleTheme}
          aria-label="Toggle dark mode"
          className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
      </div>
    </header>
  );
}
