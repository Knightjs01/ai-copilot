import { ShadowCommandPaletteProvider } from "@/components/shadow/shadow-command-palette-provider";
import { ShadowCopilotProvider } from "@/components/shadow/shadow-copilot-provider";
import { ShadowMobileNav } from "@/components/shadow/shadow-mobile-nav";
import { CandidateAuthProvider } from "@/lib/candidate-auth-context";

export default function ShadowLayout({ children }: { children: React.ReactNode }) {
  return (
    <CandidateAuthProvider>
      <ShadowCommandPaletteProvider>
        <ShadowCopilotProvider>
          <div className="pb-16 md:pb-0">{children}</div>
          <ShadowMobileNav />
        </ShadowCopilotProvider>
      </ShadowCommandPaletteProvider>
    </CandidateAuthProvider>
  );
}
