"use client";

import * as React from "react";

// Exposes the (app)/layout.tsx wrapper div that carries the `dark` class, so any Portal-based
// primitive deep inside page content (Select, Tooltip, DropdownMenu, ...) can target it as its
// Portal container without needing the ref threaded down manually through every intermediate
// component. TopNav and CommandPaletteProvider (direct children of the wrapper) keep their own
// explicit `container` props — this is additive, not a replacement for those.
const ThemeScopeContext = React.createContext<HTMLElement | null>(null);

export function ThemeScopeProvider({
  container,
  children,
}: {
  container: HTMLElement | null;
  children: React.ReactNode;
}) {
  return <ThemeScopeContext.Provider value={container}>{children}</ThemeScopeContext.Provider>;
}

export function useThemeScopeContainer() {
  return React.useContext(ThemeScopeContext);
}
