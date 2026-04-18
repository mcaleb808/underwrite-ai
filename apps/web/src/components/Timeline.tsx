"use client";

import { useMemo } from "react";

import type { LiveEvent } from "@/lib/types";

type StepKey =
  | "doc_parser"
  | "risk_assessor"
  | "guidelines_rag"
  | "decision_draft"
  | "critic";

const STEPS: { key: StepKey; label: string; description: string }[] = [
  {
    key: "doc_parser",
    label: "Reading medical documents",
    description: "Extracting key information from uploaded PDFs.",
  },
  {
    key: "risk_assessor",
    label: "Assessing risk profile",
    description: "Calculating a risk score from your details.",
  },
  {
    key: "guidelines_rag",
    label: "Looking up underwriting rules",
    description: "Matching your case to the underwriting manual.",
  },
  {
    key: "decision_draft",
    label: "Drafting your decision",
    description: "Composing a verdict with cited rules.",
  },
  {
    key: "critic",
    label: "Reviewing for fairness",
    description: "Checking the draft for bias and consistency.",
  },
];

const BAND_LABEL: Record<string, string> = {
  low: "Low risk",
  moderate: "Moderate risk",
  high: "High risk",
  very_high: "Very high risk",
};

function readableVerdict(v: unknown): string {
  if (typeof v !== "string") return "";
  return v.replace(/_/g, " ");
}

type Status = "pending" | "active" | "done" | "error";

type StepState = {
  key: StepKey;
  label: string;
  description: string;
  status: Status;
  summary: string | null;
  reruns: number;
  hasIssues: boolean;
};

function summarize(key: StepKey, latest: LiveEvent | undefined): string | null {
  if (!latest) return null;
  switch (key) {
    case "doc_parser": {
      const n = Number(latest.doc_count ?? 0);
      const errs = Number(latest.error_count ?? 0);
      if (n === 0) return "No documents to review.";
      const base = `Reviewed ${n} document${n === 1 ? "" : "s"}.`;
      return errs > 0 ? `${base} ${errs} couldn't be read.` : base;
    }
    case "risk_assessor": {
      const score = latest.score;
      const band = typeof latest.band === "string" ? BAND_LABEL[latest.band] ?? latest.band : null;
      if (typeof score === "number") {
        return band ? `${band} (score ${score.toFixed(1)} of 100).` : `Score ${score.toFixed(1)}.`;
      }
      return null;
    }
    case "guidelines_rag": {
      const n = Number(latest.chunk_count ?? 0);
      return `Matched ${n} relevant rule${n === 1 ? "" : "s"} from the manual.`;
    }
    case "decision_draft": {
      const verdict = readableVerdict(latest.verdict);
      const loading = Number(latest.premium_loading_pct ?? 0);
      const isRevision = latest.is_revision === true;
      const lead = isRevision ? "Refined to" : "Initial verdict:";
      const tail = loading ? ` (+${loading}% loading)` : "";
      return verdict ? `${lead} ${verdict}${tail}.` : null;
    }
    case "critic": {
      const issues = Number(latest.issue_count ?? 0);
      const bias = latest.bias_flag === true;
      const needsRevision = latest.needs_revision === true;
      if (issues === 0 && !bias) return "All checks passed.";
      const parts: string[] = [];
      parts.push(`${issues} concern${issues === 1 ? "" : "s"} flagged`);
      if (bias) parts.push("possible bias");
      if (needsRevision) parts.push("requested a revision");
      return parts.join(" · ") + ".";
    }
  }
}

function buildStepStates(events: LiveEvent[]): {
  steps: StepState[];
  finalized: boolean;
  failed: boolean;
} {
  const grouped: Record<StepKey, LiveEvent[]> = {
    doc_parser: [],
    risk_assessor: [],
    guidelines_rag: [],
    decision_draft: [],
    critic: [],
  };

  let finalized = false;
  let failed = false;

  for (const ev of events) {
    if (ev.node === "orchestrator") {
      if (ev.type === "finalized" || ev.type === "closed") finalized = true;
      if (ev.type === "error") failed = true;
      continue;
    }
    if (ev.node in grouped) grouped[ev.node as StepKey].push(ev);
  }

  // Determine the active step: the latest non-orchestrator event's step.
  // Once finalized, no step is "active".
  let activeKey: StepKey | null = null;
  if (!finalized) {
    for (let i = events.length - 1; i >= 0; i--) {
      const ev = events[i];
      if (ev?.node && ev.node !== "orchestrator" && (ev.node as StepKey) in grouped) {
        activeKey = ev.node as StepKey;
        break;
      }
    }
  }

  const order: StepKey[] = ["doc_parser", "risk_assessor", "guidelines_rag", "decision_draft", "critic"];
  const seenIdx = order.findIndex((k) => grouped[k].length > 0);
  const lastSeenIdx = (() => {
    let idx = -1;
    order.forEach((k, i) => {
      if (grouped[k].length > 0) idx = i;
    });
    return idx;
  })();

  const steps: StepState[] = STEPS.map((meta, i) => {
    const stepEvents = grouped[meta.key];
    const latest = stepEvents[stepEvents.length - 1];
    let status: Status = "pending";
    if (failed && stepEvents.length > 0) {
      status = "done";
    } else if (finalized) {
      status = stepEvents.length > 0 ? "done" : "pending";
    } else if (activeKey === meta.key) {
      status = "active";
    } else if (i < lastSeenIdx) {
      status = "done";
    } else if (stepEvents.length > 0 && i <= lastSeenIdx) {
      // Step has fired but isn't the latest — done.
      status = "done";
    } else if (seenIdx >= 0 && i < seenIdx) {
      status = "pending";
    }

    // For the critic, "issues > 0" should still be marked "done" but flagged.
    const hasIssues = meta.key === "critic" && Number(latest?.issue_count ?? 0) > 0;

    // Reruns = number of events on this step beyond the first.
    const reruns = Math.max(0, stepEvents.length - 1);

    return {
      key: meta.key,
      label: meta.label,
      description: meta.description,
      status,
      summary: summarize(meta.key, latest),
      reruns,
      hasIssues,
    };
  });

  return { steps, finalized, failed };
}

function StatusIcon({ status }: { status: Status }) {
  if (status === "active") {
    return (
      <span
        aria-hidden
        className="relative inline-flex h-5 w-5 items-center justify-center rounded-full bg-white dark:bg-zinc-950"
      >
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-60" />
        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-blue-500" />
      </span>
    );
  }
  if (status === "done") {
    return (
      <span
        aria-hidden
        className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-white"
      >
        <svg
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-3 w-3"
        >
          <path d="M3.5 8.5l3 3 6-6" />
        </svg>
      </span>
    );
  }
  if (status === "error") {
    return (
      <span
        aria-hidden
        className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-white"
      >
        <svg viewBox="0 0 16 16" fill="currentColor" className="h-3 w-3">
          <path d="M8 1.5a6.5 6.5 0 110 13 6.5 6.5 0 010-13zm.75 9v1.5h-1.5v-1.5h1.5zm0-6v4.5h-1.5v-4.5h1.5z" />
        </svg>
      </span>
    );
  }
  return (
    <span
      aria-hidden
      className="inline-flex h-5 w-5 items-center justify-center rounded-full border-2 border-zinc-300 bg-white dark:border-zinc-700 dark:bg-zinc-950"
    />
  );
}

export function Timeline({ events }: { events: LiveEvent[] }) {
  const { steps, finalized } = useMemo(() => buildStepStates(events), [events]);
  const allPending = steps.every((s) => s.status === "pending");

  return (
    <ol className="space-y-2">
      {steps.map((step, i) => {
        const isLast = i === steps.length - 1;
        return (
          <li key={step.key} className="grid grid-cols-[24px_1fr] gap-x-3">
            {/* icon column — connector is anchored top + bottom (no % heights) */}
            <div className="relative flex flex-col items-center">
              {!isLast ? (
                <span
                  aria-hidden
                  className="absolute left-1/2 top-7 bottom-[-12px] w-px -translate-x-1/2 bg-zinc-200 dark:bg-zinc-800"
                />
              ) : null}
              <div className="relative flex h-7 items-center">
                <StatusIcon status={step.status} />
              </div>
            </div>
            {/* content column */}
            <div
              className={`rounded-lg border px-4 py-2.5 transition-colors ${
                step.status === "active"
                  ? "border-blue-200 bg-blue-50/60 dark:border-blue-900 dark:bg-blue-950/40"
                  : step.status === "done"
                    ? "border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
                    : "border-zinc-200 bg-zinc-50/40 dark:border-zinc-800 dark:bg-zinc-950/60"
              }`}
            >
              <div className="min-w-0">
                <div className="flex items-baseline justify-between gap-3">
                  <h3
                    className={`text-sm font-medium ${
                      step.status === "pending"
                        ? "text-zinc-400 dark:text-zinc-500"
                        : "text-zinc-900 dark:text-zinc-50"
                    }`}
                  >
                    {step.label}
                  </h3>
                  {step.reruns > 0 ? (
                    <span className="shrink-0 rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                      {step.reruns === 1 ? "1 rerun" : `${step.reruns} reruns`}
                    </span>
                  ) : null}
                </div>
                <p
                  className={`mt-0.5 text-xs ${
                    step.status === "pending"
                      ? "text-zinc-400 dark:text-zinc-600"
                      : "text-zinc-500 dark:text-zinc-400"
                  }`}
                >
                  {step.summary ?? step.description}
                </p>
                {step.hasIssues && step.status === "done" ? (
                  <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                    A reviewer should double-check the flagged concerns.
                  </p>
                ) : null}
              </div>
            </div>
          </li>
        );
      })}
      {allPending ? (
        <p className="pt-2 text-center text-xs text-zinc-400 dark:text-zinc-500">
          Waiting for the pipeline to start…
        </p>
      ) : finalized ? (
        <p className="pt-2 text-center text-xs text-emerald-600 dark:text-emerald-400">
          Pipeline finished — see your decision below.
        </p>
      ) : null}
    </ol>
  );
}
