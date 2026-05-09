/** Light/dark theme toggle for the top header. */

import { useEffect, useState } from "react";
import { applyTheme, getInitialTheme, type Theme } from "../lib/theme";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  function toggle() {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }

  return (
    <button
      type="button"
      className="theme-toggle"
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      title={`Theme: ${theme}`}
      onClick={toggle}
    >
      {theme === "dark" ? "☾" : "☀"}
    </button>
  );
}
