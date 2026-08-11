import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Briefcase } from "lucide-react";

import { PhantomIcon } from "@/components/phantom-icon";
import { ShadowIcon } from "@/components/shadow-icon";

const OPTIONS = [
  {
    href: "/login/recruiter",
    title: "Recruiter / Corporate Profile",
    description:
      "Run hiring projects, screen candidates, and post Shadow jobs from your Talent Acquisition workspace.",
    cta: "Log in as a recruiter",
    icon: <Briefcase className="h-5 w-5 text-brand" />,
  },
  {
    href: "/shadow/login",
    title: "Candidate",
    description:
      "Build your Phantom Passport, browse the Shadow job board, and manage your applications — pseudonymously, on your terms.",
    cta: "Log in as a candidate",
    icon: <ShadowIcon className="h-6 w-auto" />,
  },
];

export default function LoginChooserPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-16">
      <Link href="/" aria-label="Phantom Hire home" className="mb-10 flex flex-col items-center gap-3">
        <PhantomIcon className="h-12" priority />
        <Image
          src="/phantom-wordmark.png"
          alt="Phantom Hire"
          width={829}
          height={193}
          className="h-9 w-auto"
          priority
        />
      </Link>

      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Who&apos;s logging in?
        </h1>
        <p className="max-w-md text-sm text-muted-foreground">
          Phantom Hire and Shadow are separate workspaces with separate logins — pick the one
          that&apos;s yours.
        </p>
      </div>

      <div className="mt-10 grid w-full max-w-3xl grid-cols-1 gap-4 sm:grid-cols-2">
        {OPTIONS.map((option) => (
          <Link key={option.href} href={option.href} className="group">
            <div className="flex h-full flex-col justify-between gap-6 rounded-2xl border border-border bg-white p-7 shadow-sm shadow-slate-900/[0.03] transition-all group-hover:border-brand/40 group-hover:shadow-md">
              <div className="flex flex-col gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10">
                  {option.icon}
                </div>
                <div className="flex flex-col gap-1">
                  <h2 className="text-lg font-semibold text-foreground">{option.title}</h2>
                  <p className="text-sm text-muted-foreground">{option.description}</p>
                </div>
              </div>
              <span className="inline-flex items-center gap-1.5 text-sm font-medium text-foreground">
                {option.cta}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </span>
            </div>
          </Link>
        ))}
      </div>

      <p className="mt-8 text-sm text-muted-foreground">
        New here?{" "}
        <Link href="/signup" className="font-medium text-foreground underline underline-offset-4">
          Start hiring
        </Link>{" "}
        or{" "}
        <Link href="/shadow/signup" className="font-medium text-foreground underline underline-offset-4">
          build your Passport
        </Link>
        .
      </p>
    </main>
  );
}
