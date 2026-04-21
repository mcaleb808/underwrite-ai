"use client";

import { createContext, useCallback, useContext, useRef, useState } from "react";

import { ConfirmDialog, type ConfirmOptions } from "./ConfirmDialog";
import { type Toast, Toaster, type ToastTone } from "./Toaster";

type ConfirmFn = (options: ConfirmOptions) => Promise<boolean>;
type ToastFn = (tone: ToastTone, message: string) => void;

const ConfirmContext = createContext<ConfirmFn | null>(null);
const ToastContext = createContext<ToastFn | null>(null);

export function useConfirm(): ConfirmFn {
  const ctx = useContext(ConfirmContext);
  if (!ctx) throw new Error("useConfirm must be used within <UiProvider>");
  return ctx;
}

export function useToast() {
  const push = useContext(ToastContext);
  if (!push) throw new Error("useToast must be used within <UiProvider>");
  return {
    success: (message: string) => push("success", message),
    error: (message: string) => push("error", message),
    info: (message: string) => push("info", message),
  };
}

export function UiProvider({ children }: { children: React.ReactNode }) {
  const [confirmState, setConfirmState] = useState<ConfirmOptions | null>(null);
  const resolverRef = useRef<((value: boolean) => void) | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextIdRef = useRef(1);

  const confirm = useCallback<ConfirmFn>((options) => {
    return new Promise<boolean>((resolve) => {
      // If a confirm is already pending, cancel it before replacing the resolver.
      resolverRef.current?.(false);
      resolverRef.current = resolve;
      setConfirmState(options);
    });
  }, []);

  const settle = useCallback((value: boolean) => {
    setConfirmState(null);
    const resolve = resolverRef.current;
    resolverRef.current = null;
    resolve?.(value);
  }, []);

  const push = useCallback<ToastFn>((tone, message) => {
    const id = nextIdRef.current++;
    setToasts((prev) => [...prev, { id, tone, message }]);
  }, []);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ConfirmContext.Provider value={confirm}>
      <ToastContext.Provider value={push}>
        {children}
        <ConfirmDialog
          open={confirmState !== null}
          title={confirmState?.title ?? ""}
          message={confirmState?.message ?? ""}
          confirmLabel={confirmState?.confirmLabel}
          cancelLabel={confirmState?.cancelLabel}
          tone={confirmState?.tone}
          onConfirm={() => settle(true)}
          onCancel={() => settle(false)}
        />
        <Toaster toasts={toasts} onDismiss={dismiss} />
      </ToastContext.Provider>
    </ConfirmContext.Provider>
  );
}
