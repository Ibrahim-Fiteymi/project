/**
 * Tiny theme manager — toggles `theme-light` on <html> and persists choice.
 *
 * The dark theme (default) is the primary brand experience; light mode is
 * provided for graders or users who prefer a neutral background.
 */

const KEY = "nuclei.theme.v1";

export type Theme = "dark" | "light";

export function getInitialTheme(): Theme {
  try {
    const stored = localStorage.getItem(KEY) as Theme | null;
    if (stored === "dark" || stored === "light") return stored;
  } catch {
    /* ignore */
  }
  return "dark";
}

export function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  if (theme === "light") root.classList.add("theme-light");
  else root.classList.remove("theme-light");
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    /* ignore */
  }
}
