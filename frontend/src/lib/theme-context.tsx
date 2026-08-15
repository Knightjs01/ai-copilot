"use client";

import * as React from "react";

// Hand-rolled rather than next-themes: this app has three visually distinct surfaces
// (marketing, Passport gold/navy, Shadow obsidian/blue, all hardcoded-light or page-scoped
// CSS Modules) and next-themes' default behavior of writing the theme class to <html> would
// leak dark mode into those routes on client-side navigation. This provider is mounted only
// inside (app)/layout.tsx and the caller applies the returned class to its own wrapper div.
type Theme = "light" | "dark";

const STORAGE_KEY = "phantom-ats-theme";

const ThemeContext = React.createContext<{ theme: Theme; toggleTheme: () => void } | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
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

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = React.useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
