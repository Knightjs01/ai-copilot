"use client";

import * as React from "react";
import { Moon, Search, Sun } from "lucide-react";

import { Breadcrumbs } from "@/components/breadcrumbs";
import { useCommandPalette } from "@/components/command-palette/command-palette-provider";
import { useTheme } from "@/lib/theme-context";

export function AppHeader() {
  const { theme, toggleTheme } = useTheme();
  const { openPalette } = useCommandPalette();

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
