import { ShadowAppShell } from "@/components/shadow/shadow-app-shell";

export default function ShadowCandidateLayout({ children }: { children: React.ReactNode }) {
  return <ShadowAppShell requireAuth>{children}</ShadowAppShell>;
}
