import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: "#F7F7F7",
        card: "#FFFFFF",
        primary: "#111111",
        secondary: "#666666",
        accent: "#4F46E5",
        "accent-light": "rgba(79, 70, 229, 0.1)",
      },
      fontFamily: {
        sans: [
          "SF Pro Display",
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "PingFang SC",
          "sans-serif",
        ],
      },
      maxWidth: {
        session: "900px",
      },
      borderRadius: {
        word: "12px",
        card: "16px",
        xl: "24px",
      },
      boxShadow: {
        word: "0 2px 8px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        "word-hover": "0 8px 24px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06)",
        card: "0 4px 16px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.02)",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(100%)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
