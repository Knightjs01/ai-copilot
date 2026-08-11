import { cn } from "@/lib/utils";

export function PhantomWordmark({ className }: { className?: string }) {
  return (
    <span className={cn("font-extrabold tracking-tight text-3xl", className)}>
      <span className="text-foreground">Phantom</span>{" "}
      <span className="text-brand">Hire</span>
    </span>
  );
}
