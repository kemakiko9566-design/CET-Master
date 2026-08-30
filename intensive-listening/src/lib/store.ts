import { create } from "zustand";
import type { WordData, ShadowingScore } from "./types";

export interface SessionState {
  currentSentenceIndex: number;
  isPlaying: boolean;
  playbackSpeed: number;
  wordHighlightIndex: number;
  isShadowing: boolean;
  aiPanelOpen: boolean;
  selectedWord: WordData | null;
  bottomSheetOpen: boolean;
  completedSentences: Set<number>;
  shadowingScores: Record<number, ShadowingScore>;
  totalSentences: number;
  setTotalSentences: (n: number) => void;
  nextSentence: () => void;
  prevSentence: () => void;
  setPlaying: (playing: boolean) => void;
  setSpeed: (speed: number) => void;
  setHighlight: (index: number) => void;
  toggleShadowing: () => void;
  toggleAIPanel: () => void;
  selectWord: (word: WordData) => void;
  closeBottomSheet: () => void;
  completeSentence: (index: number) => void;
  setShadowingScore: (index: number, score: ShadowingScore) => void;
  setCurrentSentenceIndex: (index: number) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  currentSentenceIndex: 0,
  isPlaying: false,
  playbackSpeed: 1,
  wordHighlightIndex: -1,
  isShadowing: false,
  aiPanelOpen: false,
  selectedWord: null,
  bottomSheetOpen: false,
  completedSentences: new Set(),
  shadowingScores: {},
  totalSentences: 0,
  setTotalSentences: (n) => set({ totalSentences: n }),
  nextSentence: () =>
    set((state) => ({
      currentSentenceIndex: Math.min(
        state.currentSentenceIndex + 1,
        state.totalSentences - 1
      ),
      wordHighlightIndex: -1,
    })),
  prevSentence: () =>
    set((state) => ({
      currentSentenceIndex: Math.max(state.currentSentenceIndex - 1, 0),
      wordHighlightIndex: -1,
    })),
  setPlaying: (playing) => set({ isPlaying: playing }),
  setSpeed: (speed) => set({ playbackSpeed: speed }),
  setHighlight: (index) => set({ wordHighlightIndex: index }),
  toggleShadowing: () =>
    set((state) => ({ isShadowing: !state.isShadowing })),
  toggleAIPanel: () =>
    set((state) => ({ aiPanelOpen: !state.aiPanelOpen })),
  selectWord: (word) =>
    set({ selectedWord: word, bottomSheetOpen: true }),
  closeBottomSheet: () =>
    set({ selectedWord: null, bottomSheetOpen: false }),
  completeSentence: (index) =>
    set((state) => {
      const next = new Set(state.completedSentences);
      next.add(index);
      return { completedSentences: next };
    }),
  setShadowingScore: (index, score) =>
    set((state) => ({
      shadowingScores: { ...state.shadowingScores, [index]: score },
    })),
  setCurrentSentenceIndex: (index) =>
    set({ currentSentenceIndex: index, wordHighlightIndex: -1 }),
}));
