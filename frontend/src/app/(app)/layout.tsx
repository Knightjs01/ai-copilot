"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { CommandPaletteProvider } from "@/components/command-palette/command-palette-provider";
import { TopNav } from "@/components/top-nav";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";
import { ThemeProvider, useTheme } from "@/lib/theme-context";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <AppLayoutInner>{children}</AppLayoutInner>
    </ThemeProvider>
  );
}

function AppLayoutInner({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const { theme } = useTheme();
  const router = useRouter();
  const wrapperRef = React.useRef<HTMLDivElement>(null);

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
    <div ref={wrapperRef} className={cn("min-h-screen bg-background", theme === "dark" && "dark")}>
      <CommandPaletteProvider container={wrapperRef.current}>
        <TopNav container={wrapperRef.current} />
        <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
      </CommandPaletteProvider>
    </div>
  );
}
