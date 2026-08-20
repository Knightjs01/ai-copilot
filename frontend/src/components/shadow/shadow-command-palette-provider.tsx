"use client";

import * as React from "react";

import { ShadowCommandPalette } from "@/components/shadow/shadow-command-palette";

interface ShadowCommandPaletteContextValue {
  openPalette: () => void;
}

const ShadowCommandPaletteContext = React.createContext<ShadowCommandPaletteContextValue | null>(
  null
);

export function ShadowCommandPaletteProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const value = React.useMemo<ShadowCommandPaletteContextValue>(
    () => ({ openPalette: () => setOpen(true) }),
    []
  );

  return (
    <ShadowCommandPaletteContext.Provider value={value}>
      {children}
      <ShadowCommandPalette open={open} onOpenChange={setOpen} />
    </ShadowCommandPaletteContext.Provider>
  );
}

export function useShadowCommandPalette() {
  const ctx = React.useContext(ShadowCommandPaletteContext);
  if (!ctx) {
    throw new Error("useShadowCommandPalette must be used within ShadowCommandPaletteProvider");
  }
  return ctx;
}
