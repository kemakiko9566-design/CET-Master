"use client";

import { ChevronLeft, ChevronRight, House } from "lucide-react";
import { cn } from "@/lib/utils";

interface TopNavBarProps {
  title: string;
  current: number;
  total: number;
  onExit: () => void;
  onNext: () => void;
  onPrev: () => void;
  className?: string;
}

export default function TopNavBar({
  title,
  current,
  total,
  onExit,
  onNext,
  onPrev,
  className,
}: TopNavBarProps) {
  return (
    <nav
      className={cn(
        "flex items-center justify-between h-14 px-4 bg-transparent select-none",
        className
      )}
    >
      <button
        onClick={onExit}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-[#E5E5E5]/50 dark:hover:bg-[#2A2A2A]/50 transition-colors text-secondary text-sm"
        aria-label="Back to CET Master"
      >
        <House className="w-4 h-4" />
        <span>返回主站</span>
      </button>

      <div className="flex flex-col items-center">
        <h1 className="text-sm font-semibold text-primary truncate max-w-[180px]">
          {title}
        </h1>
        <span className="text-xs text-secondary mt-0.5">
          Sentence {current + 1} / {total}
        </span>
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={onPrev}
          disabled={current === 0}
          className="flex items-center justify-center w-10 h-10 rounded-xl hover:bg-[#E5E5E5]/50 dark:hover:bg-[#2A2A2A]/50 transition-colors text-secondary disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Previous sentence"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <button
          onClick={onNext}
          disabled={current === total - 1}
          className="flex items-center justify-center w-10 h-10 rounded-xl hover:bg-[#E5E5E5]/50 dark:hover:bg-[#2A2A2A]/50 transition-colors text-secondary disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Next sentence"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </nav>
  );
}
