"use client";

import { useRef, useEffect, useCallback } from "react";
import { useSessionStore } from "@/lib/store";
import type { WordData } from "@/lib/types";

/**
 * Custom hook that manages audio playback and word-level highlighting.
 * Uses a real <Audio> element, seeks to sentence timestamps,
 * and updates wordHighlightIndex based on word-level timestamps.
 */
export function useAudioPlayer(
  audioUrl: string | undefined,
  currentSentenceIndex: number,
  words: WordData[],
  audioStart: number,
  audioEnd: number,
  onSentenceComplete: () => void
) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const rafRef = useRef<number>(0);
  const isPlaying = useSessionStore((s) => s.isPlaying);
  const playbackSpeed = useSessionStore((s) => s.playbackSpeed);
  const setPlaying = useSessionStore((s) => s.setPlaying);
  const setHighlight = useSessionStore((s) => s.setHighlight);

  // Create audio element once
  useEffect(() => {
    if (!audioUrl) return;
    const audio = new Audio(audioUrl);
    audio.preload = "auto";
    audioRef.current = audio;

    return () => {
      audio.pause();
      audio.src = "";
      audioRef.current = null;
    };
  }, [audioUrl]);

  // Update playback speed
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackSpeed;
    }
  }, [playbackSpeed]);

  // Seek to sentence start/end when sentence changes
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !audioUrl) return;

    // Pause and seek to start
    audio.pause();
    audio.currentTime = audioStart;
    setHighlight(-1);

    // Stop the RAF loop
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = 0;
    }
  }, [currentSentenceIndex, audioStart, audioUrl, setHighlight]);

  // Play/pause and highlight tracking
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !audioUrl) return;

    if (isPlaying) {
      // Ensure we're at the right position
      if (Math.abs(audio.currentTime - audioStart) > 0.5) {
        audio.currentTime = audioStart;
      }

      audio.play().catch(() => {
        // Auto-play blocked or no audio
        setPlaying(false);
      });

      // Word highlight loop via requestAnimationFrame
      const trackHighlight = () => {
        if (!audio || audio.paused) {
          rafRef.current = requestAnimationFrame(trackHighlight);
          return;
        }

        const ct = audio.currentTime;

        // Check if sentence is complete
        if (ct >= audioEnd) {
          audio.pause();
          setPlaying(false);
          setHighlight(-1);
          onSentenceComplete();
          return;
        }

        // Find current word by timestamp
        let foundIdx = -1;
        for (let i = 0; i < words.length; i++) {
          if (ct >= words[i].start && ct < words[i].end) {
            foundIdx = i;
            break;
          }
        }
        setHighlight(foundIdx);

        rafRef.current = requestAnimationFrame(trackHighlight);
      };

      rafRef.current = requestAnimationFrame(trackHighlight);
    } else {
      audio.pause();
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = 0;
      }
    }

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = 0;
      }
    };
  }, [isPlaying, audioUrl, audioStart, audioEnd, words, setPlaying, setHighlight, onSentenceComplete]);
}
