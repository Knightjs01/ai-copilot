import { ShadowAppShell } from "@/components/shadow/shadow-app-shell";

// Deliberately outside the shadow/(candidate) route group -- that group's shared layout always
// renders the full sidebar/header shell, and the Passport build wizard needs to feel like a
// contained walkthrough instead (no Shadow job board nav visible). Route groups don't affect the
// URL, so this still serves /shadow/passport exactly as before.
export default function PassportLayout({ children }: { children: React.ReactNode }) {
  return (
    <ShadowAppShell requireAuth chromeless>
      {children}
    </ShadowAppShell>
  );
}
