"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/auth-context";

export default function HomePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (isLoading) return;
    router.replace(user ? "/projects" : "/login");
  }, [isLoading, user, router]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50">
      <Spinner className="h-6 w-6 text-muted-foreground" />
    </main>
  );
}
