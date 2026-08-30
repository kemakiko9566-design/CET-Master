"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { Mic, Loader2, FileText, ArrowLeftFromLine } from "lucide-react";

import { useSessionStore } from "@/lib/store";
import { fetchRealtimeSession } from "@/lib/realtime-session";
import type { SessionData } from "@/lib/types";
import { useAudioPlayer } from "@/hooks/useAudioPlayer";

import TopNavBar from "@/components/TopNavBar";
import TranslationDisplay from "@/components/TranslationDisplay";
import WordCards from "@/components/WordCards";
import AudioControls from "@/components/AudioControls";
import WordBottomSheet from "@/components/WordBottomSheet";
import AIAssistant from "@/components/AIAssistant";
import ShadowingPanel from "@/components/ShadowingPanel";
import ProgressDots from "@/components/ProgressDots";
import { cn } from "@/lib/utils";

gsap.registerPlugin(useGSAP);

const sentenceVariants = {
  enter: { opacity: 0, y: 20, x: 0 },
  center: { opacity: 1, y: 0, x: 0 },
  exit: { opacity: 0, y: 0, x: -30 },
};

export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [session, setSession] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showTranscript, setShowTranscript] = useState(false);
  const [transcriptHtml, setTranscriptHtml] = useState("");

  const sentenceContainerRef = useRef<HTMLDivElement>(null);

  // Load real data
  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      const data = await fetchRealtimeSession(id);
      if (data) {
        setSession(data);
      } else {
        setError("Failed to load session data");
      }
      setLoading(false);
    }
    load();
  }, [id]);

  const {
    currentSentenceIndex,
    isPlaying,
    isShadowing,
    aiPanelOpen,
    bottomSheetOpen,
    completedSentences,
    totalSentences,
    setTotalSentences,
    nextSentence,
    prevSentence,
    setPlaying,
    setCurrentSentenceIndex,
    toggleShadowing,
    completeSentence,
  } = useSessionStore();

  useEffect(() => {
    if (session) {
      setTotalSentences(session.sentences.length);
    }
  }, [session, setTotalSentences]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " ") {
        e.preventDefault();
        if (session && currentSentenceIndex < session.sentences.length - 1) {
          nextSentence();
        }
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        if (currentSentenceIndex > 0) {
          prevSentence();
        }
      }
      if (e.key === "Escape") {
        router.push("/");
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentSentenceIndex, session, nextSentence, prevSentence, router]);

  // Used AFTER the early return where session is confirmed not null
  let _currentSentence = undefined as SessionData['sentences'][0] | undefined;
  if (session) _currentSentence = session?.sentences[currentSentenceIndex];

  const handleSentenceComplete = useCallback(() => {
    if (!session || currentSentenceIndex >= session.sentences.length) return;
    completeSentence(currentSentenceIndex);
    if (currentSentenceIndex < session.sentences.length - 1) {
      setTimeout(() => nextSentence(), 800);
    }
  }, [currentSentenceIndex, session, completeSentence, nextSentence]);

  useAudioPlayer(
    session?.audioUrl,
    currentSentenceIndex,
    _currentSentence?.words ?? [],
    _currentSentence?.audioStart ?? 0,
    _currentSentence?.audioEnd ?? 0,
    handleSentenceComplete
  );

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-bg">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-accent mx-auto mb-4" />
          <p className="text-secondary">Loading listening data...</p>
        </div>
      </main>
    );
  }

  if (!session || error) {
    return (
      <main className="min-h-screen flex items-center justify-center px-6 bg-bg">
        <div className="text-center">
          <p className="text-secondary text-lg">{error || "Session not found"}</p>
          <button
            onClick={() => router.push("/")}
            className="mt-4 text-accent hover:underline text-sm"
          >
            Back to lessons
          </button>
        </div>
      </main>
    );
  }

  const currentSentence = session.sentences[currentSentenceIndex];

  return (
    <main className="min-h-screen flex flex-col bg-bg">
      {/* Top navigation */}
      <TopNavBar
        title={session.title}
        current={currentSentenceIndex}
        total={session.sentences.length}
        onExit={() => window.open('http://localhost:8080', '_self')}
        onNext={() => {
          completeSentence(currentSentenceIndex);
          nextSentence();
        }}
        onPrev={prevSentence}
      />

      {/* Progress dots */}
      <ProgressDots
        total={session.sentences.length}
        current={currentSentenceIndex}
        completed={completedSentences}
        onDotClick={setCurrentSentenceIndex}
      />

      {/* Main content area - vertically centered */}
      <div className="flex-1 flex flex-col justify-center max-w-session mx-auto w-full">
        {/* Sentence content with animation */}
        <div ref={sentenceContainerRef} className="relative overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentSentence.id}
              variants={sentenceVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.4, ease: "easeInOut" }}
            >
              {/* Chinese translation */}
              <TranslationDisplay text={currentSentence.chinese} />

              {/* Word cards */}
              <WordCards
                words={currentSentence.words}
                sentenceIndex={currentSentenceIndex}
              />
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Audio controls */}
        <AudioControls />
      </div>

      {/* Shadowing panel */}
      <div className="max-w-session mx-auto w-full">
        <div className="flex items-center justify-center gap-3 px-4 pb-2">
          <button
            onClick={() => {
              setShowTranscript(!showTranscript);
              if (!showTranscript && !transcriptHtml && session) {
                // Load transcript
                fetch(`/api/alignment/${id}`)
                  .then((r) => r.json())
                  .then((data) => {
                    // Also fetch cleaned JSON for Chinese context
                    fetch(`/api/text/${id}`)
                      .then((r) => r.json())
                      .then((cleaned) => {
                        // Build section-to-questions map
                        const qGroups: { title: string; questions: { qn: number; opts: string }[] }[] = [];
                        (cleaned.sections || []).forEach((sec: { section_name: string; items: { type: string; question_group_title: string; questions: { question_number: number; options: Record<string, string> }[] }[] }) => {
                          (sec.items || []).forEach((item) => {
                            const opts = (item.questions || []).map(
                              (q: { question_number: number; options: Record<string, string> }) => ({
                                qn: q.question_number,
                                opts: Object.entries(q.options || {})
                                  .map(([k, v]) => `${k}. ${v}`)
                                  .join(" | "),
                              })
                            );
                            qGroups.push({ title: item.question_group_title || item.type, questions: opts });
                          });
                        });

                        let qIdx = 0;
                        let secIdx = -1;
                        const sectionNames: Record<string, string> = {
                          "Section A": "Section A 短篇新闻",
                          "Section B": "Section B 长对话",
                          "Section C": "Section C 讲座演讲",
                        };
                        const chineseTitle = cleaned.title || "听力原文";
                        let html = `<div class="text-sm font-bold text-accent mb-3 pb-2 border-b border-accent/20">${chineseTitle}</div>`;

                        (data.sentences || []).forEach((s: { text: string }) => {
                          // Detect section changes
                          const secMatch = s.text.match(/(Section [A-C])/i);
                          if (secMatch) {
                            secIdx++;
                            const label = sectionNames[secMatch[1]] || secMatch[1];
                            html += `<div class="text-xs font-semibold text-primary bg-[#F0F0F0] dark:bg-[#2A2A2A] px-3 py-1.5 rounded-md my-2">${label}</div>`;
                          }

                          // Insert question context header
                          let header = "";
                          if (qIdx < qGroups.length && new RegExp(`questions\\s+${qGroups[qIdx].questions[0]?.qn}`,'i').test(s.text)) {
                            const g = qGroups[qIdx];
                            header = `<div class="py-2 px-3 my-2 bg-accent/5 rounded-lg border border-accent/10">
                              <div class="text-xs font-bold text-accent mb-1">${g.title}</div>
                              ${g.questions.map((q: { qn: number; opts: string }) =>
                                `<div class="text-[11px] text-secondary leading-relaxed">第${q.qn}题 选项：${q.opts}</div>`
                              ).join("")}
                            </div>`;
                            qIdx++;
                          }

                          html += `${header}<div class="flex gap-3 py-2 border-b border-[#E5E5E5]/30 last:border-0">
                            <div class="flex-1 text-sm leading-relaxed text-primary">${s.text}</div>
                          </div>`;
                        });
                        setTranscriptHtml(html);
                      })
                      .catch(() => {
                        // Fallback: English only
                        const html = (data.sentences || [])
                          .map((s: { text: string }) =>
                            `<div class="text-sm leading-relaxed py-1.5 border-b border-[#E5E5E5]/50">${s.text}</div>`
                          )
                          .join("");
                        setTranscriptHtml(html);
                      });
                  })
                  .catch(() => {});
              }
            }}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-200",
              showTranscript
                ? "bg-accent text-white shadow-sm shadow-accent/30"
                : "bg-[#F0F0F0] dark:bg-[#2A2A2A] text-secondary hover:bg-[#E5E5E5] dark:hover:bg-[#333]"
            )}
          >
            <FileText className="w-4 h-4" />
            {showTranscript ? "收起原文" : "查看原文"}
          </button>
          <button
            onClick={toggleShadowing}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-200",
              isShadowing
                ? "bg-accent text-white shadow-sm shadow-accent/30"
                : "bg-[#F0F0F0] dark:bg-[#2A2A2A] text-secondary hover:bg-[#E5E5E5] dark:hover:bg-[#333]"
            )}
          >
            <Mic className="w-4 h-4" />
            {isShadowing ? "Shadowing Active" : "Shadowing"}
          </button>
        </div>
        <ShadowingPanel />
      </div>

      {/* Transcript view */}
      <AnimatePresence>
        {showTranscript && transcriptHtml && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="max-w-session mx-auto w-full overflow-hidden"
          >
            <div className="mx-4 mb-4 p-4 bg-card rounded-card border border-[#E5E5E5] dark:border-[#2A2A2A] max-h-[50vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-semibold text-secondary uppercase tracking-wider">全文对照</h3>
                <button
                  onClick={() => setShowTranscript(false)}
                  className="flex items-center gap-1 text-xs text-secondary hover:text-primary transition-colors"
                >
                  <ArrowLeftFromLine className="w-3 h-3" />
                  收起
                </button>
              </div>
              <div
                className="text-sm leading-relaxed text-primary space-y-1"
                dangerouslySetInnerHTML={{ __html: transcriptHtml }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Word bottom sheet modal */}
      <WordBottomSheet />

      {/* AI Assistant floating button + panel */}
      <AIAssistant />
    </main>
  );
}
