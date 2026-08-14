"use client";

import * as React from "react";
import { FileText, Loader2, UploadCloud } from "lucide-react";

import { cn } from "@/lib/utils";

interface DropzoneProps {
  onFileSelected: (file: File) => void;
  accept?: string;
  label: string;
  hint?: string;
  currentFileName?: string | null;
  isUploading?: boolean;
  disabled?: boolean;
  className?: string;
}

export function Dropzone({
  onFileSelected,
  accept = ".pdf,.doc,.docx",
  label,
  hint = "Drag and drop, or click to browse",
  currentFileName,
  isUploading = false,
  disabled = false,
  className,
}: DropzoneProps) {
  const [isDraggingOver, setIsDraggingOver] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (disabled || isUploading || !files || files.length === 0) return;
    const file = files[0];
    if (file) onFileSelected(file);
  };

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      onClick={() => !disabled && !isUploading && inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (!disabled && !isUploading) inputRef.current?.click();
        }
      }}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled && !isUploading) setIsDraggingOver(true);
      }}
      onDragLeave={() => setIsDraggingOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDraggingOver(false);
        handleFiles(e.dataTransfer.files);
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors",
        isDraggingOver
          ? "border-primary bg-secondary"
          // bg-background + a token-based hover border, not bg-slate-50/border-slate-300 — see
          // Card's comment in card.tsx for why hardcoded surfaces were replaced with tokens.
          : "border-border bg-background hover:border-muted-foreground/40 hover:bg-secondary",
        (disabled || isUploading) && "cursor-not-allowed opacity-60",
        className
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        disabled={disabled || isUploading}
        onChange={(e) => handleFiles(e.target.files)}
      />
      {isUploading ? (
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      ) : currentFileName ? (
        <FileText className="h-6 w-6 text-muted-foreground" />
      ) : (
        <UploadCloud className="h-6 w-6 text-muted-foreground" />
      )}
      <div className="flex flex-col gap-0.5">
        <p className="text-sm font-medium text-foreground">
          {isUploading ? "Uploading…" : currentFileName ? currentFileName : label}
        </p>
        <p className="text-xs text-muted-foreground">
          {currentFileName && !isUploading ? "Drop a new file to replace" : hint}
        </p>
      </div>
    </div>
  );
}
