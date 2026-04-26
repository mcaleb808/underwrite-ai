"use client";

import { useState } from "react";

import type { LiveEvent } from "@/lib/types";

function summarize(ev: LiveEvent): string {
  const fields = ["score", "band", "doc_count", "chunk_count", "verdict", "premium_loading_pct", "issue_count", "needs_revision", "bias_flag", "error"];
  const parts: string[] = [];
  for (const f of fields) {
    const v = (ev as Record<string, unknown>)[f];
    if (v !== undefined && v !== null && v !== "") parts.push(`${f}=${v}`);
  }
  return parts.join(" · ");
}

function typeColor(type: string): string {
  if (type === "completed" || type === "finalized") return "var(--good)";
  if (type === "error") return "var(--bad)";
  if (type === "started") return "#9aa9ff";
  return "var(--accent-2)";
}

export function EventStream({ events }: { events: LiveEvent[] }) {
  const [open, setOpen] = useState(false);
  const visible = events.filter((e) => e.node !== "orchestrator" || e.type !== "usage");

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex items-center gap-2 text-[12px] text-muted hover:text-ink"
      >
        <span>{open ? "▾" : "▸"}</span>
        <span className="mono">Event stream</span>
        <span className="text-muted-2">· {visible.length} events</span>
      </button>

      {open ? (
        <div
          className="mt-3 rounded px-5 py-4 mono text-[12px] leading-[1.7]"
          style={{ background: "var(--ink)", color: "var(--paper)" }}
        >
          <div className="flex items-center justify-between border-b pb-2 opacity-50" style={{ borderColor: "color-mix(in oklch, var(--paper) 20%, transparent)" }}>
            <span style={{ fontSize: 10, letterSpacing: "0.1em" }}>STREAM · /events</span>
            <span style={{ fontSize: 10 }}>SSE</span>
          </div>
          <div className="no-scrollbar mt-2 max-h-[260px] overflow-y-auto">
            {visible.length === 0 ? (
              <div className="opacity-60">waiting for events…</div>
            ) : (
              visible.map((ev, i) => (
                <div
                  key={i}
                  className="stream-in grid items-baseline gap-3"
                  style={{ gridTemplateColumns: "44px 130px 90px 1fr", animationDelay: `${Math.min(i * 30, 600)}ms` }}
                >
                  <span style={{ color: "var(--accent-2)" }}>#{i + 1}</span>
                  <span style={{ opacity: 0.7 }}>{ev.node}</span>
                  <span style={{ color: typeColor(ev.type) }}>{ev.type}</span>
                  <span style={{ opacity: 0.85 }}>{summarize(ev)}</span>
                </div>
              ))
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
