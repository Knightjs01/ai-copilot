import Image from "next/image";

import { cn } from "@/lib/utils";

export function ShadowIcon({
  className,
  priority,
}: {
  className?: string;
  priority?: boolean;
}) {
  return (
    <Image
      src="/shadow-icon.png"
      alt=""
      width={557}
      height={550}
      className={cn("h-8 w-auto", className)}
      priority={priority}
    />
  );
}
