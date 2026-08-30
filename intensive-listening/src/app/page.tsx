"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, Headphones, House } from "lucide-react";
import { motion } from "framer-motion";
import { availablePapers } from "@/lib/realtime-session";

export default function HomePage() {
  const router = useRouter();

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-20 relative bg-bg">
      <button
        onClick={() => window.open("http://localhost:8080", "_self")}
        className="absolute top-4 left-4 flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-[#E5E5E5]/50 dark:hover:bg-[#2A2A2A]/50 transition-colors text-secondary text-sm"
      >
        <House className="w-4 h-4" />
        <span>返回主站</span>
      </button>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="text-center mb-12"
      >
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent/10 mb-6">
          <Headphones className="w-8 h-8 text-accent" />
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-3">
          CET-4 精听训练
        </h1>
        <p className="text-base text-secondary max-w-md mx-auto leading-relaxed">
          选择一套真题开始逐句精听。每句都配有 WhisperX 词级时间戳，音频逐词高亮跟随。
        </p>
      </motion.div>

      <div className="w-full max-w-lg space-y-3">
        <h2 className="text-xs font-medium text-secondary uppercase tracking-widest mb-4 text-center">
          选择真题试卷
        </h2>
        {availablePapers.map((paper, i) => (
          <motion.button
            key={paper.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + i * 0.06, duration: 0.4 }}
            onClick={() => router.push(`/session/${paper.id}`)}
            className="w-full flex items-center justify-between p-4 rounded-card bg-card border border-[#E5E5E5] dark:border-[#2A2A2A] hover:shadow-word-hover transition-all duration-300 group text-left"
          >
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-accent bg-accent/10 px-2 py-1 rounded-md">
                {paper.year}
              </span>
              <p className="font-medium text-primary text-sm">{paper.title}</p>
            </div>
            <ArrowRight className="w-4 h-4 text-secondary group-hover:text-accent group-hover:translate-x-1 transition-all" />
          </motion.button>
        ))}
      </div>
    </main>
  );
}
