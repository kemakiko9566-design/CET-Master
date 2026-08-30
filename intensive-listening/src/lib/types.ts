export interface WordData {
  text: string;
  start: number;
  end: number;
  definition?: string;
  pronunciation?: string;
  level?: "CET4" | "CET6" | "Advanced";
  root?: string;
  synonyms?: string[];
  collocations?: string[];
  example?: string;
  aiExplanation?: string;
}

export interface SentenceData {
  id: string;
  chinese: string;
  english: string;
  words: WordData[];
  audioStart: number;
  audioEnd: number;
}

export interface SessionData {
  id: string;
  title: string;
  sentences: SentenceData[];
  audioUrl: string;
}

export interface ShadowingScore {
  accuracy: number;
  fluency: number;
  stress: number;
  intonation: number;
}
