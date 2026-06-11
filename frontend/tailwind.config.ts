import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bss: {
          bg: "#0B1020",
          card: "#111827",
          line: "#1F2937",
          text: "#F9FAFB",
          muted: "#9CA3AF",
          green: "#22C55E",
          yellow: "#EAB308",
          red: "#EF4444",
          accent: "#3B82F6",
          cyan: "#06B6D4",
        },
      },
      animation: {
        "soft-pulse": "soft-pulse 2.4s ease-in-out infinite",
        "spin-slow": "spin 8s linear infinite",
        "glow-pulse": "glow-pulse 3s infinite",
      },
      keyframes: {
        "soft-pulse": {
          "0%,100%": { opacity: "0.85" },
          "50%": { opacity: "1" },
        },
        "glow-pulse": {
          "0%, 100%": { boxShadow: "0 0 15px rgba(6, 182, 212, 0.2)" },
          "50%": { boxShadow: "0 0 25px rgba(6, 182, 212, 0.5)" },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
