"use client";

import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast";
import { useToastQueue } from "@/lib/toast-context";

export function Toaster() {
  const { toasts, dismissToast } = useToastQueue();

  return (
    <ToastProvider>
      {toasts.map(({ id, title, description, variant }) => (
        <Toast
          key={id}
          variant={variant}
          onOpenChange={(open) => !open && dismissToast(id)}
        >
          <div className="flex flex-col gap-0.5">
            <ToastTitle>{title}</ToastTitle>
            {description && <ToastDescription>{description}</ToastDescription>}
          </div>
          <ToastClose />
        </Toast>
      ))}
      <ToastViewport />
    </ToastProvider>
  );
}
