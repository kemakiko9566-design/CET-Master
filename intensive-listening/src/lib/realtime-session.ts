/**
 * Load real CET-4 listening data from aligned JSON + cleaned JSON.
 * Uses WhisperX word-level timestamps for precise audio highlighting.
 */
import type { SentenceData, SessionData, WordData } from "./types";

interface AlignedSentence {
  id: string;
  start: number;
  end: number;
  text: string;
  words: { w: string; start: number; end: number }[];
}

interface AlignedData {
  paper_id: string;
  sentences: AlignedSentence[];
}

interface CleanedItem {
  item_id: string;
  type: string;
  paragraphs: string[];
  question_group_title: string;
  questions: {
    question_number: number;
    question_text: string;
    options: Record<string, string>;
  }[];
}

interface CleanedSection {
  section_name: string;
  items: CleanedItem[];
}

interface CleanedData {
  paper_id: string;
  title: string;
  sections: CleanedSection[];
}

/** Parse paper_id to build MP3 path (served from public/audio/) */
function getMp3Path(paperId: string): string {
  return `/audio/${paperId}.mp3`;
}

/** Check if a sentence is a "direction" (intro/instruction) vs. actual content */
function isDirectionSentence(text: string): boolean {
  const lower = text.toLowerCase().trim();
  const directionMarkers = [
    "directions:",
    "in this section,",
    "in this part,",
    "you will hear",
    "you must then choose",
    "then mark the corresponding",
    "both the conversation",
    "both the passage",
    "will be spoken only once",
    "will be spoken twice",
    "at the end of",
    "you will read",
    "are based on",
    "is based on",
    "questions",
    "section a",
    "section b",
    "section c",
    "part ii",
    "part iii",
    "college english test band 4",
    "listening comprehension",
  ];
  for (const marker of directionMarkers) {
    if (lower.startsWith(marker) || lower.includes(marker)) return true;
  }
  // Empty or very short text
  if (text.length < 15) return true;
  return false;
}

/** Build realistic mock sentences from aligned data for demo purposes */
function buildSentences(aligned: AlignedData, text: string): SentenceData[] {
  const sentences: SentenceData[] = [];
  let sentenceCounter = 0;

  for (const s of aligned.sentences) {
    if (isDirectionSentence(s.text)) continue;
    if (s.words.length < 3) continue;
    if (s.end - s.start > 30) continue; // skip very long segments

    sentenceCounter++;
    const words: WordData[] = s.words.map((w) => ({
      text: w.w,
      start: w.start,
      end: w.end,
      definition: "",
      pronunciation: "",
      level: "CET4" as const,
    }));

    sentences.push({
      id: `s${sentenceCounter}`,
      chinese: "", // Chinese translation not available from aligned data
      english: s.text,
      words,
      audioStart: s.start,
      audioEnd: s.end,
    });

    // Limit to 30 sentences per session for manageable UX
    if (sentenceCounter >= 30) break;
  }

  return sentences;
}

/** Fetch and build a real session from paper data */
export async function fetchRealtimeSession(paperId: string): Promise<SessionData | null> {
  try {
    const [alignedRes, cleanedRes] = await Promise.all([
      fetch(`/api/alignment/${paperId}`),
      fetch(`/api/text/${paperId}`),
    ]);

    if (!alignedRes.ok || !cleanedRes.ok) {
      console.warn("Failed to load real data, falling back");
      return null;
    }

    const aligned: AlignedData = await alignedRes.json();
    const cleaned: CleanedData = await cleanedRes.json();

    const sentences = buildSentences(aligned, "");
    if (sentences.length === 0) return null;

    const mp3 = getMp3Path(paperId);

    return {
      id: paperId,
      title: cleaned.title || paperId,
      sentences,
      audioUrl: mp3,
    };
  } catch (e) {
    console.error("Error loading real session:", e);
    return null;
  }
}

/** Pre-built session configs */
export const availablePapers = [
  { id: "cet4_2024_12_1", title: "2024年12月 听力真题（第1套）", year: "2024" },
  { id: "cet4_2024_12_2", title: "2024年12月 听力真题（第2套）", year: "2024" },
  { id: "cet4_2024_06_1", title: "2024年6月 听力真题（第1套）", year: "2024" },
  { id: "cet4_2024_06_2", title: "2024年6月 听力真题（第2套）", year: "2024" },
  { id: "cet4_2025_06_1", title: "2025年6月 听力真题（第1套）", year: "2025" },
  { id: "cet4_2025_12_1", title: "2025年12月 听力真题（第1套）", year: "2025" },
];
