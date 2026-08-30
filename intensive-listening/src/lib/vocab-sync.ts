/**
 * Vocabulary sync between Intensive Listening App and CET Master main site.
 * Both share the same localStorage key "cet4_master_data" so words added here
 * automatically appear in the main site's 生词本 (Vocab) view.
 */

const STORE_KEY = "cet4_master_data";

interface VocabWord {
  id: string;
  text: string;
  category: string; // 'L' | 'R' | 'W'
  context: string;
  timestamp: number;
  reviewCount: number;
}

interface MasterState {
  words: VocabWord[];
  [key: string]: unknown;
}

function genId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

/** Load the shared vocab state from localStorage */
function loadMasterState(): MasterState {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return { words: [] };
}

/** Save the shared vocab state */
function saveMasterState(state: MasterState): void {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(state));
  } catch { /* ignore */ }
}

/** Check if a word already exists in the shared vocab */
export function isWordInVocab(word: string): boolean {
  const state = loadMasterState();
  return state.words.some((w: VocabWord) => w.text === word);
}

/** Add a word to the shared vocab (main site's 生词本) */
export function addWordToMasterVocab(
  word: string,
  category: "L" | "R" | "W" = "L",
  context: string = ""
): void {
  const state = loadMasterState();
  if (state.words.some((w: VocabWord) => w.text === word)) return; // already exists

  state.words.unshift({
    id: genId(),
    text: word.toLowerCase(),
    category,
    context,
    timestamp: Date.now(),
    reviewCount: 0,
  });

  saveMasterState(state);
}

/** Get all vocab words count */
export function getVocabCount(): number {
  return loadMasterState().words.length;
}
