"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, X, Send, Bot, User } from "lucide-react";
import { useSessionStore } from "@/lib/store";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const placeholderResponses: Record<string, string> = {
  default:
    "This word is used in the context of environmental discussions. Try to notice how it's pronounced in the sentence and pay attention to its collocations.",
};

export default function AIAssistant() {
  const aiPanelOpen = useSessionStore((s) => s.aiPanelOpen);
  const toggleAIPanel = useSessionStore((s) => s.toggleAIPanel);
  const selectedWord = useSessionStore((s) => s.selectedWord);

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm your AI learning assistant. Ask me anything about the words, grammar, or pronunciation in this lesson.",
    },
  ]);
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (aiPanelOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [aiPanelOpen]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            selectedWord
              ? `"${selectedWord.text}" - ${placeholderResponses.default}`
              : placeholderResponses.default,
        },
      ]);
    }, 600);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Floating button */}
      <button
        onClick={toggleAIPanel}
        className={cn(
          "fixed bottom-6 right-6 z-30 flex items-center justify-center w-12 h-12 rounded-full shadow-lg shadow-accent/30 transition-all duration-200",
          aiPanelOpen
            ? "bg-[#E5E5E5] dark:bg-[#2A2A2A] text-secondary"
            : "bg-accent text-white hover:scale-105 active:scale-95"
        )}
        aria-label="AI Assistant"
      >
        {aiPanelOpen ? (
          <X className="w-5 h-5" />
        ) : (
          <Sparkles className="w-5 h-5" />
        )}
      </button>

      {/* Panel */}
      <AnimatePresence>
        {aiPanelOpen && (
          <motion.div
            initial={{ opacity: 0, x: 320 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 320 }}
            transition={{ type: "spring", damping: 26, stiffness: 260 }}
            className="fixed right-0 top-0 bottom-0 z-20 w-full max-w-sm bg-card border-l border-[#E5E5E5] dark:border-[#2A2A2A] shadow-xl flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center gap-3 px-5 py-4 border-b border-[#E5E5E5] dark:border-[#2A2A2A]">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent/10">
                <Bot className="w-4 h-4 text-accent" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-primary">AI Assistant</h3>
                <p className="text-xs text-secondary">Ask anything about the lesson</p>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={cn(
                    "flex gap-2.5",
                    msg.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  {msg.role === "assistant" && (
                    <div className="w-7 h-7 rounded-full bg-accent/10 flex items-center justify-center shrink-0 mt-1">
                      <Bot className="w-3.5 h-3.5 text-accent" />
                    </div>
                  )}
                  <div
                    className={cn(
                      "max-w-[80%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed",
                      msg.role === "user"
                        ? "bg-accent text-white rounded-tr-md"
                        : "bg-[#F0F0F0] dark:bg-[#2A2A2A] text-primary rounded-tl-md"
                    )}
                  >
                    {msg.content}
                  </div>
                  {msg.role === "user" && (
                    <div className="w-7 h-7 rounded-full bg-accent flex items-center justify-center shrink-0 mt-1">
                      <User className="w-3.5 h-3.5 text-white" />
                    </div>
                  )}
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="px-4 py-3 border-t border-[#E5E5E5] dark:border-[#2A2A2A]">
              <div className="flex items-center gap-2 bg-[#F0F0F0] dark:bg-[#2A2A2A] rounded-xl px-3 py-1.5">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a question..."
                  className="flex-1 bg-transparent text-sm text-primary placeholder:text-secondary outline-none"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent text-white disabled:opacity-40 disabled:cursor-not-allowed transition-opacity shrink-0"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
