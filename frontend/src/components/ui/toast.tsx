"use client";

import * as React from "react";
import * as ToastPrimitive from "@radix-ui/react-toast";
import { cva, type VariantProps } from "class-variance-authority";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";

const ToastProvider = ToastPrimitive.Provider;

// Unlike Dialog/Select/DropdownMenu, @radix-ui/react-toast has no exported Portal — Viewport
// renders in place. That's fine here: Toaster is already mounted inside the themed wrapper div
// in (app)/layout.tsx, so the .dark CSS-variable scope cascades to it naturally, and `fixed`
// positioning still stacks correctly regardless of DOM position.
function ToastViewport({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof ToastPrimitive.Viewport>) {
  return (
    <ToastPrimitive.Viewport
      className={cn(
        "fixed bottom-0 right-0 z-[100] flex max-h-screen w-full flex-col gap-2 p-4 sm:max-w-sm",
        className
      )}
      {...props}
    />
  );
}

const toastVariants = cva(
  "flex items-start gap-3 rounded-xl border p-4 shadow-xl shadow-slate-900/10 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[swipe=end]:animate-out",
  {
    variants: {
      variant: {
        default: "border-border bg-card text-foreground",
        success: "border-success/20 bg-success/10 text-foreground",
        danger: "border-danger/20 bg-danger/10 text-foreground",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

function Toast({
  className,
  variant,
  ...props
}: React.ComponentPropsWithoutRef<typeof ToastPrimitive.Root> & VariantProps<typeof toastVariants>) {
  return (
    <ToastPrimitive.Root className={cn(toastVariants({ variant }), className)} {...props} />
  );
}

function ToastTitle({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof ToastPrimitive.Title>) {
  return (
    <ToastPrimitive.Title
      className={cn("text-sm font-semibold text-foreground", className)}
      {...props}
    />
  );
}

function ToastDescription({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof ToastPrimitive.Description>) {
  return (
    <ToastPrimitive.Description
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}

function ToastClose({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof ToastPrimitive.Close>) {
  return (
    <ToastPrimitive.Close
      className={cn(
        "ml-auto shrink-0 rounded-full p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground",
        className
      )}
      {...props}
    >
      <X className="h-3.5 w-3.5" />
    </ToastPrimitive.Close>
  );
}

export { ToastProvider, ToastViewport, Toast, ToastTitle, ToastDescription, ToastClose };
