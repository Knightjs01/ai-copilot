import * as React from "react";
import Image from "next/image";
import Link from "next/link";

export function ShadowAuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-16">
      <div className="mb-8 flex flex-col items-center gap-3">
        <Link href="/shadow" aria-label="Shadow home" className="flex flex-col items-center gap-3">
          <Image
            src="/phantom-shadow-logo-new.png"
            alt="Phantom Shadow: Anonymous Talent Network"
            width={2172}
            height={724}
            className="h-16 w-auto sm:h-20"
            priority
          />
        </Link>
      </div>
      <div className="w-full max-w-sm rounded-2xl border border-border bg-white p-8 shadow-sm shadow-slate-900/[0.03]">
        <div className="mb-6 flex flex-col gap-1">
          <h1 className="text-xl font-semibold tracking-tight text-foreground">{title}</h1>
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        </div>
        {children}
      </div>
      <div className="mt-6 text-sm text-muted-foreground">{footer}</div>
    </main>
  );
}
