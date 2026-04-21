"use client";

import { useEffect, useState } from "react";

export type Usage = {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  calls: number;
};

const EMPTY: Usage = {
  prompt_tokens: 0,
  completion_tokens: 0,
  total_tokens: 0,
  cost_usd: 0,
  calls: 0,
};

function formatTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

function formatCost(usd: number): string {
  if (usd === 0) return "$0";
  if (usd < 0.001) return "<$0.001";
  if (usd < 0.01) return `$${usd.toFixed(4)}`;
  return `$${usd.toFixed(3)}`;
}

function formatElapsed(ms: number): string {
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  return `${m}m ${s % 60}s`;
}

export function UsagePill({
  usage,
  startedAt,
  finished,
}: {
  usage?: Usage;
  startedAt: number;
  finished: boolean;
}) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (finished) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [finished]);

  const u = usage ?? EMPTY;
  const elapsed = now - startedAt;

  return (
    <div className="inline-flex items-center gap-3 rounded-full border border-zinc-200 bg-white px-3 py-1 text-[11px] font-medium text-zinc-600 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-400">
      <span className="tabular-nums" title={`${u.total_tokens} tokens across ${u.calls} calls`}>
        <span className="text-zinc-400 dark:text-zinc-500">tokens</span>{" "}
        <span className="text-zinc-900 dark:text-zinc-50">{formatTokens(u.total_tokens)}</span>
      </span>
      <span className="text-zinc-300 dark:text-zinc-700">·</span>
      <span className="tabular-nums" title="Estimated cost in USD">
        <span className="text-zinc-400 dark:text-zinc-500">cost</span>{" "}
        <span className="text-zinc-900 dark:text-zinc-50">{formatCost(u.cost_usd)}</span>
      </span>
      <span className="text-zinc-300 dark:text-zinc-700">·</span>
      <span className="tabular-nums">
        <span className="text-zinc-400 dark:text-zinc-500">elapsed</span>{" "}
        <span className="text-zinc-900 dark:text-zinc-50">{formatElapsed(elapsed)}</span>
      </span>
    </div>
  );
}
