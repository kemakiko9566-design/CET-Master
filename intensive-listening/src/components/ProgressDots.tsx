"use client";

import { cn } from "@/lib/utils";

interface ProgressDotsProps {
  total: number;
  current: number;
  completed: Set<number>;
  onDotClick?: (index: number) => void;
}

export default function ProgressDots({
  total,
  current,
  completed,
  onDotClick,
}: ProgressDotsProps) {
  if (total === 0) return null;

  return (
    <div className="flex items-center justify-center gap-1.5 py-3">
      {Array.from({ length: total }, (_, i) => (
        <button
          key={i}
          onClick={() => onDotClick?.(i)}
          className={cn(
            "w-2 h-2 rounded-full transition-all duration-300",
            i === current && "bg-accent scale-125",
            i < current && completed.has(i) && "bg-[#D1D5DB] dark:bg-[#4B5563]",
            i < current && !completed.has(i) && "bg-[#E5E5E5] dark:bg-[#374151]",
            i > current && "bg-[#E5E5E5] dark:bg-[#374151]",
            onDotClick && "cursor-pointer hover:scale-150"
          )}
          aria-label={`Go to sentence ${i + 1}`}
        />
      ))}
    </div>
  );
}
