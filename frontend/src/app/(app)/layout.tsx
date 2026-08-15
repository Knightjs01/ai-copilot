"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { CommandPaletteProvider } from "@/components/command-palette/command-palette-provider";
import { Toaster } from "@/components/toaster";
import { TopNav } from "@/components/top-nav";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";
import { ThemeProvider, useTheme } from "@/lib/theme-context";
import { ThemeScopeProvider } from "@/lib/theme-scope-context";
import { ToastQueueProvider } from "@/lib/toast-context";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <ToastQueueProvider>
        <AppLayoutInner>{children}</AppLayoutInner>
      </ToastQueueProvider>
    </ThemeProvider>
  );
}

function AppLayoutInner({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const { theme } = useTheme();
  const router = useRouter();
  // A plain useRef doesn't itself trigger a re-render when it attaches, so children reading
  // wrapperRef.current at render time can get a stale null on the render where it first becomes
  // available and never pick up the real node until something UNRELATED happens to re-render
  // this component. A state-backed callback ref makes attachment itself a real re-render, so
  // every consumer of this DOM node (Portal `container` targets, for the .dark CSS-variable
  // scope) reliably sees the populated value.
  const [wrapper, setWrapper] = React.useState<HTMLDivElement | null>(null);

  React.useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login/recruiter");
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className={cn("flex min-h-screen items-center justify-center bg-background", theme === "dark" && "dark")}>
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div ref={setWrapper} className={cn("min-h-screen bg-background", theme === "dark" && "dark")}>
      <CommandPaletteProvider container={wrapper}>
        <TopNav container={wrapper} />
        <ThemeScopeProvider container={wrapper}>
          <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
        </ThemeScopeProvider>
      </CommandPaletteProvider>
      <Toaster />
    </div>
  );
}
