"use client";

import { useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import type { WordData } from "@/lib/types";
import { useSessionStore } from "@/lib/store";
import { cn } from "@/lib/utils";

interface WordCardsProps {
  words: WordData[];
  sentenceIndex: number;
}

export default function WordCards({ words, sentenceIndex }: WordCardsProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const selectWord = useSessionStore((s) => s.selectWord);
  const wordHighlightIndex = useSessionStore((s) => s.wordHighlightIndex);

  const handleWordClick = useCallback(
    (word: WordData) => {
      selectWord(word);
    },
    [selectWord]
  );

  useGSAP(
    () => {
      if (!containerRef.current) return;
      const cards = containerRef.current.querySelectorAll(".word-card");
      gsap.fromTo(
        cards,
        { opacity: 0, y: 16, scale: 0.95 },
        {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.4,
          stagger: 0.05,
          ease: "back.out(1.4)",
        }
      );
    },
    { dependencies: [words, sentenceIndex], scope: containerRef }
  );

  // GSAP pulse animation on highlighted word
  useEffect(() => {
    if (wordHighlightIndex < 0 || !containerRef.current) return;
    const cards = containerRef.current.querySelectorAll(".word-card");
    const target = cards[wordHighlightIndex] as HTMLElement;
    if (!target) return;
    gsap.fromTo(
      target,
      { scale: 1 },
      { scale: 1.08, duration: 0.15, yoyo: true, repeat: 1, ease: "power2.out" }
    );
  }, [wordHighlightIndex]);

  return (
    <div
      ref={containerRef}
      className="flex flex-wrap justify-center gap-2 px-4 py-4 max-w-2xl mx-auto"
    >
      {words.map((word, i) => (
        <motion.button
          key={`${sentenceIndex}-${i}`}
          layout
          whileHover={{ y: -2, scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => handleWordClick(word)}
          className={cn(
            "word-card inline-block px-3 py-2 rounded-word bg-card border border-[#E5E5E5] dark:border-[#2A2A2A] shadow-word hover:shadow-word-hover transition-shadow duration-200 text-sm sm:text-base font-medium text-primary cursor-pointer select-none",
            wordHighlightIndex === i && "ring-2 ring-accent bg-accent/5"
          )}
        >
          {word.text}
        </motion.button>
      ))}
    </div>
  );
}
