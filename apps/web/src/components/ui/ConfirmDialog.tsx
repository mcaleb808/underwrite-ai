"use client";

import { useEffect, useRef } from "react";

export type ConfirmTone = "default" | "destructive";

export type ConfirmOptions = {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: ConfirmTone;
};

type Props = ConfirmOptions & {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  tone = "default",
  onConfirm,
  onCancel,
}: Props) {
  const ref = useRef<HTMLDialogElement | null>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        onCancel();
      }}
      onClose={onCancel}
      className="rounded-xl border border-zinc-200 bg-white p-0 shadow-2xl backdrop:bg-zinc-950/50 backdrop:backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950"
    >
      <div className="w-[min(92vw,420px)] p-5">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">{title}</h3>
        <p className="mt-2 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">{message}</p>
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-300 dark:hover:bg-zinc-900"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            autoFocus
            className={
              tone === "destructive"
                ? "rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700"
                : "rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
            }
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  );
}
