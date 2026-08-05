"use client";

import * as React from "react";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";

import { cn } from "@/lib/utils";

interface KanbanColumnProps {
  id: string;
  title: string;
  count: number;
  children: React.ReactNode;
  className?: string;
}

export function KanbanColumn({ id, title, count, children, className }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex w-72 shrink-0 flex-col gap-3 rounded-2xl border border-transparent p-2 transition-colors",
        isOver && "border-primary/30 bg-secondary/60",
        className
      )}
    >
      <div className="flex items-center gap-2 px-2 pt-1">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <span className="rounded-full bg-secondary px-2 py-0.5 text-xs font-medium text-muted-foreground">
          {count}
        </span>
      </div>
      <div className="flex flex-col gap-2">{children}</div>
    </div>
  );
}

interface KanbanCardProps {
  id: string;
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export function KanbanCard({ id, children, onClick, className }: KanbanCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id });

  const style = transform
    ? { transform: CSS.Translate.toString(transform), zIndex: 50 }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={onClick}
      className={cn(
        "cursor-grab rounded-2xl border border-border bg-white p-3.5 shadow-sm shadow-slate-900/[0.03] transition-shadow active:cursor-grabbing",
        isDragging && "opacity-50 shadow-lg",
        onClick && "hover:border-slate-300",
        className
      )}
    >
      {children}
    </div>
  );
}
