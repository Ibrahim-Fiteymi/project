/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--bg-base)",
        foreground: "var(--text-primary)",
        muted: {
          DEFAULT: "var(--surface-glass)",
          foreground: "var(--text-muted)",
        },
        border: "var(--border-hairline)",
        input: "var(--border-hairline)",
        ring: "var(--accent-violet)",
        primary: {
          DEFAULT: "var(--accent-teal)",
          foreground: "#0b0f1a",
        },
      },
      borderRadius: {
        lg: "var(--radius-card)",
        md: "var(--radius-tile)",
        sm: "var(--radius-input)",
      },
    },
  },
  plugins: [],
};
