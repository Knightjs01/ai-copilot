import { Briefcase, CheckCircle2, EyeOff } from "lucide-react";

const CANDIDATE_BENEFITS = [
  "Free forever. Building a Passport and applying through Shadow never costs you anything.",
  "No recruiter spam. You apply to roles you choose, not the other way around.",
  "Real salary ranges upfront, not withheld until the final stage.",
  "You control every reveal. Nothing about your identity moves without your approval.",
];

const COMPANY_BENEFITS = [
  "Reach people who aren't applying anywhere else. Shadow is built for passive and privacy-conscious talent, not just active job seekers.",
  "Run a genuinely confidential search. List a role without naming your company until you're ready.",
  "No résumé database to maintain. Every applicant arrives with a reviewed, approved Passport, not a raw CV dump.",
  "Every applicant lands straight in Phantom ATS, ranked by evidence, ready to screen.",
];

export function ShadowBenefitsSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">Built for both sides</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            A marketplace that works whichever side you&apos;re on.
          </h2>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-7 shadow-sm shadow-slate-900/[0.03]">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <EyeOff className="h-4 w-4" />
              </div>
              <h3 className="text-base font-semibold text-foreground">For candidates</h3>
            </div>
            <ul className="flex flex-col gap-3">
              {CANDIDATE_BENEFITS.map((benefit) => (
                <li key={benefit} className="flex items-start gap-2.5">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                  <span className="text-sm leading-relaxed text-muted-foreground">{benefit}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-7 shadow-sm shadow-slate-900/[0.03]">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <Briefcase className="h-4 w-4" />
              </div>
              <h3 className="text-base font-semibold text-foreground">For companies</h3>
            </div>
            <ul className="flex flex-col gap-3">
              {COMPANY_BENEFITS.map((benefit) => (
                <li key={benefit} className="flex items-start gap-2.5">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                  <span className="text-sm leading-relaxed text-muted-foreground">{benefit}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
