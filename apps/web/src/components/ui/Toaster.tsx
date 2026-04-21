"use client";

import { useEffect, useState } from "react";

export type ToastTone = "success" | "error" | "info";

export type Toast = {
  id: number;
  tone: ToastTone;
  message: string;
};

const TONE_STYLES: Record<ToastTone, string> = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/70 dark:text-emerald-100",
  error: "border-red-200 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950/70 dark:text-red-100",
  info: "border-zinc-200 bg-white text-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-100",
};

export function Toaster({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div
      role="region"
      aria-label="Notifications"
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
    >
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={() => onDismiss(t.id)} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: () => void }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const show = window.setTimeout(() => setVisible(true), 10);
    const hide = window.setTimeout(onDismiss, 4000);
    return () => {
      window.clearTimeout(show);
      window.clearTimeout(hide);
    };
  }, [onDismiss]);

  return (
    <div
      role={toast.tone === "error" ? "alert" : "status"}
      className={`pointer-events-auto flex items-start gap-3 rounded-lg border px-4 py-3 text-sm shadow-lg transition-all duration-200 ${
        TONE_STYLES[toast.tone]
      } ${visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"}`}
    >
      <span className="flex-1">{toast.message}</span>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss"
        className="shrink-0 text-xs opacity-60 hover:opacity-100"
      >
        ×
      </button>
    </div>
  );
}
