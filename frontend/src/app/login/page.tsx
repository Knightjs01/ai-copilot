import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { PhantomIcon } from "@/components/phantom-icon";

export const metadata: Metadata = {
  title: "Log in | Phantom Hire",
};

const OPTIONS = [
  {
    href: "/shadow/login",
    title: "Candidate",
    description:
      "Build your Phantom Passport, browse the Shadow job board, and manage your applications, pseudonymously, on your terms.",
    cta: "Log in as a Candidate",
    logo: {
      src: "/shadow-wordmark.png",
      alt: "Shadow: Anonymous Job Board",
      width: 1525,
      height: 550,
      // Single line of icon+text fills nearly the whole canvas, so a modest box height
      // already reads at full size.
      heightClass: "h-12",
    },
  },
  {
    href: "/login/recruiter",
    title: "Recruiter - Talent ATS",
    description:
      "Run hiring projects, screen candidates, and post Shadow jobs from your Talent Acquisition workspace.",
    cta: "Log in as a Recruiter",
    logo: {
      src: "/phantom-ats-wordmark.png",
      alt: "Phantom ATS",
      width: 1388,
      height: 339,
      // The big "Phantom" wordmark only occupies the top ~70% of this canvas -- the rest is
      // the much smaller "HIRE" subscript -- so matching Shadow's box height by pixels alone
      // renders "Phantom" visibly smaller than Shadow's single-line mark. A taller box gets
      // the actual readable word to a comparable size.
      heightClass: "h-[70px]",
    },
  },
];

export default function LoginChooserPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-16">
      <Link href="/" aria-label="Phantom Hire home" className="mb-10 flex flex-col items-center gap-3">
        <PhantomIcon className="h-12" priority />
        <Image
          src="/phantom-ats-wordmark.png"
          alt="Phantom Hire"
          width={1388}
          height={339}
          className="h-9 w-auto"
          priority
        />
      </Link>

      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Who&apos;s logging in?
        </h1>
        <p className="max-w-md text-sm text-muted-foreground">
          Phantom Hire and Shadow are separate workspaces with separate logins. Pick the one
          that&apos;s yours.
        </p>
      </div>

      <div className="mt-10 grid w-full max-w-3xl grid-cols-1 gap-4 sm:grid-cols-2">
        {OPTIONS.map((option) => (
          <Link key={option.href} href={option.href} className="group">
            <div className="flex h-full flex-col justify-between gap-6 rounded-2xl border border-border bg-white p-7 shadow-sm shadow-slate-900/[0.03] transition-all group-hover:border-brand/40 group-hover:shadow-md">
              <div className="flex flex-col gap-4">
                <Image
                  src={option.logo.src}
                  alt={option.logo.alt}
                  width={option.logo.width}
                  height={option.logo.height}
                  className={`${option.logo.heightClass} w-auto self-start`}
                />
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
