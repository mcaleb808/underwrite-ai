"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createApplicationFromPersona } from "@/lib/api";

export function RunButton({ personaId }: { personaId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    setLoading(true);
    setError(null);
    try {
      const res = await createApplicationFromPersona(personaId);
      router.push(`/applications/${res.task_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "unknown error");
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={onClick}
        disabled={loading}
        className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-50 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {loading ? "running…" : "run underwriting"}
      </button>
      {error ? (
        <span className="text-xs text-red-600 dark:text-red-400">{error}</span>
      ) : null}
    </div>
  );
}
