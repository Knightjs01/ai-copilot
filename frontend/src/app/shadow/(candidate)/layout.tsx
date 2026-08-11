"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { ShadowTopNav } from "@/components/shadow/shadow-top-nav";
import { Spinner } from "@/components/ui/spinner";
import { useCandidateAuth } from "@/lib/candidate-auth-context";

export default function ShadowCandidateLayout({ children }: { children: React.ReactNode }) {
  const { candidate, isLoading } = useCandidateAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (!isLoading && !candidate) {
      router.replace("/shadow/login");
    }
  }, [isLoading, candidate, router]);

  if (isLoading || !candidate) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <ShadowTopNav />
      <main className="mx-auto max-w-4xl px-6 py-10">{children}</main>
    </div>
  );
}
