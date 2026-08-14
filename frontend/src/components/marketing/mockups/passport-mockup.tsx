import { Lock, ShieldCheck, Vault } from "lucide-react";

import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

// Deliberately not design-system tokens — this is a one-off dark/gold treatment for the
// flagship Passport showcase, kept local to this file rather than added to globals.css or
// tailwind.config so it stays obviously contained and doesn't read as a supported second theme.
const SKILLS = ["Distributed Systems", "Go", "Platform Architecture"];

const PRIVATE_FIELDS = ["Name & photo", "Current employer"];

export function PassportMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/passport" badge="Live now">
      <div className="-m-4 rounded-xl bg-[#0b1220] p-4 sm:-m-6 sm:p-6">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-3.5">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-[#d4af6a]/60 text-xs font-semibold text-[#d4af6a]">
              P-78
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-white">Pulse-78</p>
              <p className="truncate text-[11px] text-white/50">
                Senior Backend Engineer · Remote
              </p>
            </div>
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border-2 border-[#d4af6a]/40">
              <span className="text-[11px] font-semibold text-[#d4af6a]">92%</span>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 p-3.5">
            <div className="flex items-center gap-2.5">
              <Vault className="h-4 w-4 shrink-0 text-[#d4af6a]" />
              <p className="text-sm font-medium text-white">Candidate Vault</p>
            </div>
            <span className="shrink-0 rounded-full bg-[#d4af6a]/10 px-2.5 py-1 text-[11px] font-semibold text-[#d4af6a]">
              Approved · Version 3
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {SKILLS.map((skill) => (
              <span
                key={skill}
                className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] text-white/80"
              >
                {skill}
              </span>
            ))}
          </div>

          <div className="flex flex-col gap-1.5 rounded-xl border border-white/10 bg-white/5 p-3.5">
            <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-white/50">
              <ShieldCheck className="h-3.5 w-3.5 text-[#d4af6a]" />
              What stays private
            </p>
            {PRIVATE_FIELDS.map((field) => (
              <p key={field} className="flex items-center gap-1.5 text-xs text-white/70">
                <Lock className="h-3 w-3 shrink-0 text-white/40" />
                {field}
              </p>
            ))}
          </div>
        </div>
      </div>
    </BrowserFrame>
  );
}
