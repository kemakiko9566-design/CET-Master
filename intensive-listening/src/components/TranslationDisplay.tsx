"use client";

import { motion } from "framer-motion";

interface TranslationDisplayProps {
  text: string;
}

export default function TranslationDisplay({ text }: TranslationDisplayProps) {
  return (
    <motion.div
      key={text}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="text-center px-4 py-6"
    >
      <p className="text-3xl sm:text-4xl font-semibold text-secondary leading-relaxed">
        {text}
      </p>
    </motion.div>
  );
}
