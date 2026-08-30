"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Square, Volume2, CheckCircle2 } from "lucide-react";
import { useSessionStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import type { ShadowingScore } from "@/lib/types";

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-secondary">{label}</span>
        <span className="text-xs font-semibold text-primary">{pct}%</span>
      </div>
      <div className="h-2 rounded-full bg-[#E5E5E5] dark:bg-[#2A2A2A] overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="h-full rounded-full bg-accent"
        />
      </div>
    </div>
  );
}

export default function ShadowingPanel() {
  const isShadowing = useSessionStore((s) => s.isShadowing);
  const toggleShadowing = useSessionStore((s) => s.toggleShadowing);
  const currentSentenceIndex = useSessionStore((s) => s.currentSentenceIndex);
  const shadowingScores = useSessionStore((s) => s.shadowingScores);
  const setShadowingScore = useSessionStore((s) => s.setShadowingScore);

  const [isRecording, setIsRecording] = useState(false);
  const [hasRecorded, setHasRecorded] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const currentScore = shadowingScores[currentSentenceIndex];

  const handleRecordToggle = () => {
    if (isRecording) {
      setIsRecording(false);
      setHasRecorded(true);
      if (timerRef.current) clearTimeout(timerRef.current);

      // Simulate a shadowing score
      const score: ShadowingScore = {
        accuracy: 0.65 + Math.random() * 0.3,
        fluency: 0.6 + Math.random() * 0.35,
        stress: 0.55 + Math.random() * 0.4,
        intonation: 0.5 + Math.random() * 0.45,
      };
      setShadowingScore(currentSentenceIndex, score);
    } else {
      setIsRecording(true);
      setHasRecorded(false);
    }
  };

  return (
    <AnimatePresence>
      {isShadowing && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.3 }}
          className="overflow-hidden border-t border-[#E5E5E5] dark:border-[#2A2A2A]"
        >
          <div className="px-6 py-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Volume2 className="w-4 h-4 text-accent" />
                <span className="text-sm font-semibold text-primary">Shadowing Practice</span>
              </div>
              <button
                onClick={toggleShadowing}
                className="text-xs text-secondary hover:text-primary transition-colors"
              >
                Close
              </button>
            </div>

            {/* Record button */}
            <div className="flex items-center justify-center gap-4">
              <button
                onClick={handleRecordToggle}
                className={cn(
                  "flex items-center justify-center w-16 h-16 rounded-full transition-all duration-200",
                  isRecording
                    ? "bg-red-500 text-white shadow-lg shadow-red-500/30 animate-pulse"
                    : "bg-accent text-white shadow-lg shadow-accent/30 hover:scale-105 active:scale-95"
                )}
                aria-label={isRecording ? "Stop recording" : "Start recording"}
              >
                {isRecording ? (
                  <Square className="w-5 h-5" />
                ) : (
                  <Mic className="w-6 h-6" />
                )}
              </button>
            </div>

            {isRecording && (
              <p className="text-center text-xs text-red-500 font-medium animate-pulse">
                Recording... Speak clearly into your microphone
              </p>
            )}

            {hasRecorded && !isRecording && (
              <div className="flex items-center justify-center gap-2 text-xs text-green-600 dark:text-green-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>Recording saved. You can review your scores below.</span>
              </div>
            )}

            {/* Scores */}
            {currentScore && (
              <div className="space-y-3 p-4 rounded-xl bg-[#F0F0F0] dark:bg-[#2A2A2A]">
                <p className="text-xs font-semibold text-secondary uppercase tracking-wider">
                  Your Scores
                </p>
                <div className="space-y-2.5">
                  <ScoreBar label="Accuracy" value={currentScore.accuracy} />
                  <ScoreBar label="Fluency" value={currentScore.fluency} />
                  <ScoreBar label="Stress" value={currentScore.stress} />
                  <ScoreBar label="Intonation" value={currentScore.intonation} />
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
