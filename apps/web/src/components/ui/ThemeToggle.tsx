"use client";

import { useSyncExternalStore } from "react";

type Theme = "light" | "dark";

const COOKIE = "theme";
const ONE_YEAR = 60 * 60 * 24 * 365;

function readCookie(): Theme | null {
  const match = document.cookie.match(/(?:^|;\s*)theme=(light|dark)/);
  return (match?.[1] as Theme | undefined) ?? null;
}

function readSystem(): Theme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(t: Theme) {
  document.documentElement.setAttribute("data-theme", t);
  document.cookie = `${COOKIE}=${t}; Path=/; Max-Age=${ONE_YEAR}; SameSite=Lax`;
  window.dispatchEvent(new Event("theme-change"));
}

const subscribe = (cb: () => void) => {
  const mql = window.matchMedia("(prefers-color-scheme: dark)");
  mql.addEventListener("change", cb);
  window.addEventListener("theme-change", cb);
  return () => {
    mql.removeEventListener("change", cb);
    window.removeEventListener("theme-change", cb);
  };
};

const getSnapshot = (): Theme => readCookie() ?? readSystem();
const getServerSnapshot = (): Theme => "light";

export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const next: Theme = theme === "dark" ? "light" : "dark";
  const label = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";

  return (
    <button
      type="button"
      onClick={() => applyTheme(next)}
      aria-label={label}
      title={label}
      className="grid h-8 w-8 place-items-center rounded-full border border-line bg-paper text-ink transition-colors hover:bg-paper-2"
    >
      {theme === "dark" ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
        </svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      )}
    </button>
  );
}
