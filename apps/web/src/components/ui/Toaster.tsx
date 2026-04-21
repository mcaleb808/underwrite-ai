"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { useIsClient } from "./useIsClient";

export type ToastTone = "success" | "error" | "info";

export type Toast = {
  id: number;
  tone: ToastTone;
  message: string;
};

const TONE_STYLES: Record<ToastTone, string> = {
  success:
    "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/70 dark:text-emerald-100",
  error:
    "border-red-200 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950/70 dark:text-red-100",
  info: "border-zinc-200 bg-white text-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100",
};

const SHOW_DELAY_MS = 10;
const DISMISS_AFTER_MS = 4000;

export function Toaster({
  toasts,
  onDismiss,
}: {
  toasts: Toast[];
  onDismiss: (id: number) => void;
}) {
  const mounted = useIsClient();
  if (!mounted) return null;

  return createPortal(
    <div
      role="region"
      aria-label="Notifications"
      className="pointer-events-none fixed left-1/2 top-4 z-50 flex w-full max-w-sm -translate-x-1/2 flex-col items-center gap-2 px-4"
    >
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>,
    document.body,
  );
}

function ToastItem({
  toast,
  onDismiss,
}: {
  toast: Toast;
  onDismiss: (id: number) => void;
}) {
  const [visible, setVisible] = useState(false);
  // Stash the latest onDismiss so the dismiss timer arms exactly once per
  // toast — a new onDismiss identity from the parent must not reset it.
  const dismissRef = useRef(onDismiss);
  useEffect(() => {
    dismissRef.current = onDismiss;
  }, [onDismiss]);

  useEffect(() => {
    const show = window.setTimeout(() => setVisible(true), SHOW_DELAY_MS);
    const hide = window.setTimeout(() => dismissRef.current(toast.id), DISMISS_AFTER_MS);
    return () => {
      window.clearTimeout(show);
      window.clearTimeout(hide);
    };
  }, [toast.id]);

  return (
    <div
      role={toast.tone === "error" ? "alert" : "status"}
      className={`pointer-events-auto flex w-full items-start gap-3 rounded-lg border px-4 py-3 text-sm shadow-lg transition-all duration-200 ${
        TONE_STYLES[toast.tone]
      } ${visible ? "translate-y-0 opacity-100" : "-translate-y-2 opacity-0"}`}
    >
      <span className="flex-1">{toast.message}</span>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss"
        className="shrink-0 text-xs opacity-60 hover:opacity-100"
      >
        ×
      </button>
    </div>
  );
}
