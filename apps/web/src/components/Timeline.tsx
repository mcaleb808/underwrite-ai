"use client";

import type { LiveEvent } from "@/lib/types";

const NODE_LABELS: Record<string, string> = {
  doc_parser: "Document parser",
  risk_assessor: "Risk assessor",
  guidelines_rag: "Guidelines retrieval",
  decision_draft: "Decision draft",
  critic: "Adversarial critic",
  orchestrator: "Orchestrator",
};

function summarize(event: LiveEvent): string {
  switch (event.type) {
    case "parsed":
      return `parsed ${event.doc_count ?? 0} document(s)`;
    case "score":
      return `score ${event.score ?? "?"} (${event.band ?? "?"})`;
    case "retrieved":
      return `retrieved ${event.chunk_count ?? 0} guideline chunks`;
    case "drafted":
      return `verdict: ${event.verdict ?? "?"} (loading ${event.premium_loading_pct ?? 0}%)${
        event.is_revision ? " — revision" : ""
      }`;
    case "reviewed":
      return `${event.issue_count ?? 0} issue(s)${
        event.bias_flag ? ", bias flagged" : ""
      }${event.needs_revision ? " — revision requested" : ""}`;
    case "started":
      return "pipeline started";
    case "finalized":
      return `finalized: ${event.verdict ?? "?"}`;
    case "closed":
      return "stream closed";
    case "error":
      return `error: ${event.error ?? "unknown"}`;
    default:
      return event.type;
  }
}

export function Timeline({ events }: { events: LiveEvent[] }) {
  if (events.length === 0) {
    return (
      <p className="text-sm text-zinc-500 dark:text-zinc-400">waiting for events…</p>
    );
  }

  return (
    <ol className="space-y-2">
      {events.map((event, i) => (
        <li
          key={i}
          className="flex items-baseline gap-3 rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-800 dark:bg-zinc-950"
        >
          <span className="w-6 text-xs text-zinc-400">{i + 1}.</span>
          <span className="w-44 shrink-0 font-medium text-zinc-900 dark:text-zinc-50">
            {NODE_LABELS[event.node] ?? event.node}
          </span>
          <span className="text-zinc-600 dark:text-zinc-400">{summarize(event)}</span>
        </li>
      ))}
    </ol>
  );
}
