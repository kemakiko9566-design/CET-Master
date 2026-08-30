"use client";

import { useCallback, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Volume2, BookmarkPlus, BookmarkCheck } from "lucide-react";
import { useSessionStore } from "@/lib/store";
import { isWordInVocab, addWordToMasterVocab } from "@/lib/vocab-sync";
import { lookupLocal } from "@/data/cet4-dictionary";
import { cn } from "@/lib/utils";

export default function WordBottomSheet() {
  const { selectedWord, bottomSheetOpen, closeBottomSheet } = useSessionStore();
  const [added, setAdded] = useState(false);
  const [dictEntry, setDictEntry] = useState<ReturnType<typeof lookupLocal>>(null);

  useEffect(() => {
    if (selectedWord) {
      setAdded(isWordInVocab(selectedWord.text));
      // Instant local dictionary lookup
      const entry = lookupLocal(selectedWord.text);
      setDictEntry(entry);
    }
  }, [selectedWord]);

  const handleAddVocab = useCallback(() => {
    if (!selectedWord || added) return;
    addWordToMasterVocab(selectedWord.text, "L", selectedWord.example || "");
    setAdded(true);
  }, [selectedWord, added]);

  if (!selectedWord) return null;

  return (
    <AnimatePresence>
      {bottomSheetOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/20 z-40 backdrop-blur-sm"
            onClick={closeBottomSheet}
          />

          {/* Sheet */}
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-50 bg-card rounded-t-2xl shadow-xl max-h-[80vh] overflow-y-auto"
          >
            <div className="relative p-6 pb-8 max-w-lg mx-auto">
              {/* Close button */}
              <button
                onClick={closeBottomSheet}
                className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-full hover:bg-[#F0F0F0] dark:hover:bg-[#2A2A2A] transition-colors text-secondary"
              >
                <X className="w-4 h-4" />
              </button>

              {/* Word */}
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-2xl font-bold text-primary">{selectedWord.text}</h2>
                {(selectedWord.pronunciation || dictEntry?.pronunciation) && (
                  <button className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center text-accent hover:bg-accent/20 transition-colors">
                    <Volume2 className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Pronunciation */}
              {(selectedWord.pronunciation || dictEntry?.pronunciation) && (
                <p className="text-sm text-accent font-medium mb-3">
                  {selectedWord.pronunciation || dictEntry?.pronunciation}
                </p>
              )}

              {/* Level badge */}
              {(selectedWord.level || dictEntry?.level) && (
                <span className="inline-block text-[10px] font-semibold uppercase tracking-wider text-accent bg-accent/10 px-2 py-0.5 rounded-md mb-4">
                  {dictEntry?.level || selectedWord.level}
                </span>
              )}

              {/* Chinese translation — local dictionary (instant, no API) */}
              {dictEntry ? (
                <div className="mb-4 p-3 bg-accent/5 rounded-xl border border-accent/10">
                  <p className="text-xs font-medium text-secondary uppercase tracking-wider mb-1">中文释义</p>
                  <p className="text-lg font-medium text-primary">{dictEntry.definition}</p>
                </div>
              ) : (
                <div className="mb-4 p-3 bg-[#F5F5F5] dark:bg-[#222] rounded-xl">
                  <p className="text-xs font-medium text-secondary uppercase tracking-wider mb-1">中文释义</p>
                  <p className="text-sm text-secondary">词库暂无收录</p>
                </div>
              )}

              {/* Word root — from local dict */}
              {dictEntry?.root && (
                <div className="mb-3">
                  <p className="text-xs font-medium text-secondary uppercase tracking-wider mb-1">词根</p>
                  <p className="text-sm text-primary">{dictEntry.root}</p>
                </div>
              )}

              {/* Synonyms */}
              {selectedWord.synonyms && selectedWord.synonyms.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-medium text-secondary uppercase tracking-wider mb-1">同义词</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedWord.synonyms.map((s) => (
                      <span key={s} className="text-xs px-2 py-1 bg-[#F0F0F0] dark:bg-[#2A2A2A] rounded-md text-secondary">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Collocations */}
              {selectedWord.collocations && selectedWord.collocations.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-medium text-secondary uppercase tracking-wider mb-1">常用搭配</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedWord.collocations.map((c) => (
                      <span key={c} className="text-xs px-2 py-1 bg-accent/5 rounded-md text-accent font-medium">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Example */}
              {selectedWord.example && (
                <div className="mb-4">
                  <p className="text-xs font-medium text-secondary uppercase tracking-wider mb-1">例句</p>
                  <p className="text-sm text-primary italic border-l-2 border-accent/30 pl-3">{selectedWord.example}</p>
                </div>
              )}

              {/* AI Explanation */}
              {selectedWord.aiExplanation && (
                <div className="mb-5 p-3 bg-[#F5F5F5] dark:bg-[#222] rounded-xl">
                  <p className="text-xs font-medium text-secondary uppercase tracking-wider mb-1">AI 解析</p>
                  <p className="text-sm text-primary leading-relaxed">{selectedWord.aiExplanation}</p>
                </div>
              )}

              {/* Add to master vocab button */}
              <button
                onClick={handleAddVocab}
                disabled={added}
                className={cn(
                  "w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-semibold text-sm transition-all duration-200",
                  added
                    ? "bg-[#E5E5E5] dark:bg-[#333] text-secondary cursor-default"
                    : "bg-accent text-white hover:bg-accent/90 active:scale-[0.98] shadow-sm"
                )}
              >
                {added ? (
                  <>
                    <BookmarkCheck className="w-4 h-4" />
                    已在主站生词本中
                  </>
                ) : (
                  <>
                    <BookmarkPlus className="w-4 h-4" />
                    加入主站生词本
                  </>
                )}
              </button>

              <p className="text-[10px] text-secondary text-center mt-2">
                已同步到 CET Master 主站生词本 · 共 {isWordInVocab(selectedWord.text) ? "" : ""}个单词
              </p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
