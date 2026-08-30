"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
} from "lucide-react";
import { useSessionStore } from "@/lib/store";
import { cn } from "@/lib/utils";

const speeds = [0.5, 0.75, 1, 1.25];

function WaveformBars({ isPlaying }: { isPlaying: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const barsRef = useRef<number[]>([]);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const barCount = 48;
    if (barsRef.current.length === 0) {
      barsRef.current = Array.from({ length: barCount }, () => Math.random() * 0.5 + 0.25);
    }

    const animate = () => {
      if (!ctx || !canvas) return;
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const barW = w / barCount - 1.5;
      barsRef.current.forEach((val, i) => {
        const x = i * (barW + 1.5);
        const barH = val * h * 0.8;
        const y = (h - barH) / 2;

        if (isPlaying) {
          barsRef.current[i] += (Math.random() - 0.5) * 0.15;
          barsRef.current[i] = Math.max(0.1, Math.min(1, barsRef.current[i]));
        }

        const gradient = ctx.createLinearGradient(x, y, x, y + barH);
        gradient.addColorStop(0, "#4F46E5");
        gradient.addColorStop(1, "#6366F1");
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barW, barH, 2);
        ctx.fill();
      });

      rafRef.current = requestAnimationFrame(animate);
    };

    animate();
    return () => cancelAnimationFrame(rafRef.current);
  }, [isPlaying]);

  return (
    <canvas
      ref={canvasRef}
      width={240}
      height={48}
      className="w-full max-w-[240px] h-12 mx-auto"
    />
  );
}

export default function AudioControls() {
  const {
    isPlaying,
    playbackSpeed,
    setPlaying,
    setSpeed,
    nextSentence,
    prevSentence,
  } = useSessionStore();

  return (
    <div className="flex flex-col items-center gap-4 px-4 py-6 select-none">
      <WaveformBars isPlaying={isPlaying} />

      {/* Speed selector */}
      <div className="flex items-center gap-1.5">
        {speeds.map((s) => (
          <button
            key={s}
            onClick={() => setSpeed(s)}
            className={cn(
              "px-3 py-1 text-xs font-medium rounded-full transition-all duration-200",
              playbackSpeed === s
                ? "bg-accent text-white shadow-sm"
                : "bg-[#F0F0F0] dark:bg-[#2A2A2A] text-secondary hover:bg-[#E5E5E5] dark:hover:bg-[#333]"
            )}
          >
            {s}x
          </button>
        ))}
      </div>

      {/* Main controls */}
      <div className="flex items-center gap-4">
        <button
          onClick={prevSentence}
          className="flex items-center justify-center w-10 h-10 rounded-full text-secondary hover:bg-[#F0F0F0] dark:hover:bg-[#2A2A2A] transition-colors"
          aria-label="Previous"
        >
          <SkipBack className="w-5 h-5" />
        </button>

        <button
          onClick={() => setPlaying(!isPlaying)}
          className="flex items-center justify-center w-14 h-14 rounded-full bg-accent text-white shadow-lg shadow-accent/30 hover:shadow-accent/40 hover:scale-105 active:scale-95 transition-all duration-200"
          aria-label={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? (
            <Pause className="w-6 h-6" />
          ) : (
            <Play className="w-6 h-6 ml-0.5" />
          )}
        </button>

        <button
          onClick={nextSentence}
          className="flex items-center justify-center w-10 h-10 rounded-full text-secondary hover:bg-[#F0F0F0] dark:hover:bg-[#2A2A2A] transition-colors"
          aria-label="Next"
        >
          <SkipForward className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
