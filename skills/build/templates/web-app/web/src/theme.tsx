import { useState } from "react";

// Every app offers light and dark. The choice is `data-theme` on
// <html> (styles.css redefines the tokens under it), remembered per
// browser; with no choice saved, the OS setting decides.
type Theme = "light" | "dark";
const KEY = "theme";

function saved(): Theme | null {
  try {
    const value = localStorage.getItem(KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

function current(): Theme {
  return (
    saved() ??
    (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
  );
}

// Called once in main.tsx before the first render, so a saved choice
// never flashes the other scheme.
export function applySavedTheme() {
  const theme = saved();
  if (theme) document.documentElement.dataset.theme = theme;
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(current);
  const next: Theme = theme === "dark" ? "light" : "dark";
  return (
    <button
      className="ghost"
      aria-label={`Switch to ${next} mode`}
      title={`Switch to ${next} mode`}
      onClick={() => {
        document.documentElement.dataset.theme = next;
        try {
          localStorage.setItem(KEY, next);
        } catch {
          // Storage blocked: the choice lasts until reload.
        }
        setTheme(next);
      }}
    >
      {theme === "dark" ? "☀︎" : "☾"}
    </button>
  );
}
