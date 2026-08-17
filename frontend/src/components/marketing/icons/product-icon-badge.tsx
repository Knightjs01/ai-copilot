import { cn } from "@/lib/utils";

export function ProductIconBadge({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex h-16 w-16 shrink-0 items-center justify-center rounded-3xl shadow-lg shadow-brand/25",
        className
      )}
      style={{ background: "linear-gradient(135deg, hsl(253 58% 70%), hsl(253 45% 40%))" }}
    >
      {children}
    </div>
  );
}
