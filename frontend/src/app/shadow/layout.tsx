"use client";

import * as React from "react";

import { ShadowCommandPaletteProvider } from "@/components/shadow/shadow-command-palette-provider";
import { ShadowCopilotProvider } from "@/components/shadow/shadow-copilot-provider";
import { CandidateAuthProvider } from "@/lib/candidate-auth-context";
import { ShadowThemeProvider, useShadowTheme } from "@/lib/shadow-theme-context";
import { ThemeScopeProvider } from "@/lib/theme-scope-context";
import { cn } from "@/lib/utils";

export default function ShadowLayout({ children }: { children: React.ReactNode }) {
  return (
    <ShadowThemeProvider>
      <CandidateAuthProvider>
        <ShadowThemeWrapper>{children}</ShadowThemeWrapper>
      </CandidateAuthProvider>
    </ShadowThemeProvider>
  );
}

// Mirrors (app)/layout.tsx's AppLayoutInner wrapper pattern: a state-backed callback ref so
// Portal-based primitives (command palette, dropdown menus) reliably get a non-null container the
// moment the DOM node exists, carrying the literal "dark" class scoped only to Shadow's tree.
function ShadowThemeWrapper({ children }: { children: React.ReactNode }) {
  const { theme } = useShadowTheme();
  const [wrapper, setWrapper] = React.useState<HTMLDivElement | null>(null);

  return (
    <div ref={setWrapper} className={cn("min-h-screen bg-background", theme === "dark" && "dark")}>
      <ShadowCommandPaletteProvider container={wrapper}>
        <ShadowCopilotProvider>
          <ThemeScopeProvider container={wrapper}>{children}</ThemeScopeProvider>
        </ShadowCopilotProvider>
      </ShadowCommandPaletteProvider>
    </div>
  );
}
