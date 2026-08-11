import Image from "next/image";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export function JobSeekersCtaSection() {
  return (
    <section className="border-t border-border bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto flex flex-col items-center gap-5 rounded-3xl border border-border bg-white px-8 py-14 text-center shadow-sm shadow-slate-900/[0.03]">
          <Image
            src="/shadow-icon.png"
            alt=""
            width={557}
            height={550}
            className="h-10 w-auto"
          />
          <h2 className="max-w-xl text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            Ready to explore your next move, quietly?
          </h2>
          <p className="max-w-lg text-muted-foreground">
            Build your Phantom Passport once, apply anywhere on Shadow, and stay a Callsign until
            you choose to reveal yourself.
          </p>
          <Button asChild variant="brand" size="lg">
            <Link href="/shadow/signup">Build your Phantom Passport</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
