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
        className="btn"
        style={{ padding: "8px 14px", fontSize: 12 }}
      >
        {loading ? "Running…" : "Run →"}
      </button>
      {error ? (
        <span className="text-[11px]" style={{ color: "var(--bad)" }}>
          {error}
        </span>
      ) : null}
    </div>
  );
}
