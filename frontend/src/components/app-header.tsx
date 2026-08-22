"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Globe, LogOut, Moon, Search, Sun } from "lucide-react";

import { Breadcrumbs } from "@/components/breadcrumbs";
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
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { useTheme } from "@/lib/theme-context";

export function AppHeader() {
  const { theme, toggleTheme } = useTheme();
  const { openPalette } = useCommandPalette();
  const { user, logout } = useAuth();
  const router = useRouter();
  const container = useThemeScopeContainer();

  const handleLogout = async () => {
    await logout();
    router.push("/login/recruiter");
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-4 border-b border-border bg-background/80 px-6 backdrop-blur">
      <Breadcrumbs />

      <div className="flex items-center gap-2">
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

        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                aria-label="Account menu"
                className="flex items-center gap-2 rounded-full px-2 py-1 text-left transition-colors hover:bg-secondary"
              >
                <Avatar name={user.full_name} className="h-7 w-7 text-xs" />
                <span className="max-w-[10rem] truncate text-sm font-medium text-foreground">
                  {user.full_name}
                </span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent container={container} align="end" side="bottom">
              <DropdownMenuLabel>{user.full_name}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={() => router.push("/settings")}>Settings</DropdownMenuItem>
              <DropdownMenuItem onSelect={() => router.push("/")}>
                <Globe className="h-3.5 w-3.5" />
                Back to Phantom Hire
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
