"use client";

import * as React from "react";

// Structural copy of lib/theme-context.tsx, kept as its own instance rather than shared with the
// ATS's ThemeProvider: separate localStorage key so a candidate and a recruiter sharing a browser
// don't collide, and mounted only inside shadow/layout.tsx so dark mode stays scoped to Shadow's
// route tree, same reasoning as the ATS one being scoped to (app)/layout.tsx.
type Theme = "light" | "dark";

const STORAGE_KEY = "phantom-shadow-theme";

const ShadowThemeContext = React.createContext<{ theme: Theme; toggleTheme: () => void } | null>(
  null
);

export function ShadowThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = React.useState<Theme>("light");

  React.useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "dark" || stored === "light") setTheme(stored);
  }, []);

  const toggleTheme = React.useCallback(() => {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      window.localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  }, []);

  const value = React.useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme]);

  return <ShadowThemeContext.Provider value={value}>{children}</ShadowThemeContext.Provider>;
}

export function useShadowTheme() {
  const ctx = React.useContext(ShadowThemeContext);
  if (!ctx) throw new Error("useShadowTheme must be used within ShadowThemeProvider");
  return ctx;
}
