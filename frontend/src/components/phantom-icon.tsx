import Image from "next/image";

import { cn } from "@/lib/utils";

export function PhantomIcon({
  className,
  priority,
}: {
  className?: string;
  priority?: boolean;
}) {
  return (
    <Image
      src="/phantom-icon.png"
      alt=""
      width={668}
      height={844}
      className={cn("h-3.5 w-auto", className)}
      priority={priority}
    />
  );
}
