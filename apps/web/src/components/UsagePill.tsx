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
    <div className="mono inline-flex items-center gap-3 rounded-full border border-line bg-paper px-3.5 py-1.5 text-[11px] text-ink-2">
      <span className="tnum" title={`${u.total_tokens} tokens across ${u.calls} calls`}>
        <span className="text-muted">tokens</span>{" "}
        <span className="text-ink">{formatTokens(u.total_tokens)}</span>
      </span>
      <span className="text-muted-2">·</span>
      <span className="tnum" title="Estimated cost in USD">
        <span className="text-muted">cost</span>{" "}
        <span className="text-ink">{formatCost(u.cost_usd)}</span>
      </span>
      <span className="text-muted-2">·</span>
      <span className="tnum">
        <span className="text-muted">elapsed</span>{" "}
        <span className="text-ink">{formatElapsed(elapsed)}</span>
      </span>
    </div>
  );
}
