/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        // Deep "code editor" base (GitHub-dark inspired, NOT purple)
        canvas: {
          base: "#0a0e14",
          panel: "#0d1117",
          raised: "#11161f",
          inset: "#161b22",
        },
        // Primary accent: ACCEPTED green (like a passing test / LeetCode AC)
        accent: {
          DEFAULT: "#22c55e",
          bright: "#4ade80",
          deep: "#16a34a",
          dim: "#15803d",
        },
        // Secondary: cyan for "bridge" connections / links
        bridge: {
          DEFAULT: "#22d3ee",
          deep: "#06b6d4",
        },
        // Difficulty amber (ratings, warnings)
        warn: {
          DEFAULT: "#f59e0b",
          bright: "#fbbf24",
          deep: "#d97706",
        },
        // Hard / destructive rose
        danger: { DEFAULT: "#fb7185", deep: "#f43f5e" },
        // Neutrals (cool slate, no violet/purple tint)
        ink: {
          DEFAULT: "#e6edf3",
          muted: "#8b949e",
          faint: "#6e7681",
        },
        line: {
          DEFAULT: "rgba(255,255,255,0.08)",
          strong: "rgba(255,255,255,0.14)",
        },
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 24px -12px rgba(0,0,0,0.6)",
        glow: "0 0 0 1px rgba(34,197,94,0.35), 0 8px 30px -8px rgba(34,197,94,0.25)",
      },
      keyframes: {
        blink: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0" } },
        shimmer: { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
        rise: { "0%": { opacity: "0", transform: "translateY(12px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        glowPulse: { "0%,100%": { opacity: "0.45" }, "50%": { opacity: "0.85" } },
        dash: { to: { strokeDashoffset: "0" } },
      },
      animation: {
        blink: "blink 1.1s step-end infinite",
        shimmer: "shimmer 2s linear infinite",
        rise: "rise 0.45s cubic-bezier(0.16,1,0.3,1) both",
        glowPulse: "glowPulse 5s ease-in-out infinite",
        dash: "dash 1.4s ease-out forwards",
      },
    },
  },
  plugins: [],
};
