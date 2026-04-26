import type { LiveEvent } from "./types";

export type StepKey =
  | "doc_parser"
  | "risk_assessor"
  | "guidelines_rag"
  | "decision_draft"
  | "critic";

export type StepStatus = "pending" | "active" | "done" | "error";

export type StepMeta = {
  key: StepKey;
  short: string;
  label: string;
  description: string;
};

export const STEPS: StepMeta[] = [
  {
    key: "doc_parser",
    short: "Doc parser",
    label: "Reading medical documents",
    description: "Extracting key information from uploaded PDFs.",
  },
  {
    key: "risk_assessor",
    short: "Risk model",
    label: "Assessing risk profile",
    description: "Calculating a risk score from your details.",
  },
  {
    key: "guidelines_rag",
    short: "Guidelines",
    label: "Looking up underwriting rules",
    description: "Matching your case to the underwriting manual.",
  },
  {
    key: "decision_draft",
    short: "Decision",
    label: "Drafting your decision",
    description: "Composing a verdict with cited rules.",
  },
  {
    key: "critic",
    short: "Critic",
    label: "Reviewing for fairness",
    description: "Checking the draft for bias and consistency.",
  },
];

export type StepState = {
  key: StepKey;
  short: string;
  label: string;
  description: string;
  status: StepStatus;
  summary: string | null;
  reruns: number;
  hasIssues: boolean;
  errorMessage: string | null;
  latest: LiveEvent | undefined;
};

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
      const band =
        typeof latest.band === "string" ? BAND_LABEL[latest.band] ?? latest.band : null;
      if (typeof score === "number") {
        return band
          ? `${band} (score ${score.toFixed(1)} of 100).`
          : `Score ${score.toFixed(1)}.`;
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

export function humanizeError(raw: unknown): string {
  const text = typeof raw === "string" ? raw : "";
  if (/timeout|timed out/i.test(text)) {
    return "The AI service didn't respond in time. We've already retried once - try running this again.";
  }
  if (/rate.?limit|429/i.test(text)) {
    return "We hit the AI provider's rate limit. Wait a moment and run this again.";
  }
  if (/openrouter|openai|anthropic/i.test(text)) {
    return "The AI provider returned an error. Check the provider status and re-run this case.";
  }
  return "This step couldn't complete. Re-run the case to try again.";
}

export function buildStepStates(events: LiveEvent[]): {
  steps: StepState[];
  finalized: boolean;
  failed: boolean;
} {
  // SSE replays history on reconnect; only score the latest run.
  let runStart = 0;
  for (let i = events.length - 1; i >= 0; i--) {
    const ev = events[i];
    if (ev?.node === "orchestrator" && ev.type === "started") {
      runStart = i;
      break;
    }
  }
  const currentEvents = events.slice(runStart);

  const grouped: Record<StepKey, LiveEvent[]> = {
    doc_parser: [],
    risk_assessor: [],
    guidelines_rag: [],
    decision_draft: [],
    critic: [],
  };

  let finalized = false;
  let failed = false;

  for (const ev of currentEvents) {
    if (ev.node === "orchestrator") {
      if (ev.type === "finalized" || ev.type === "closed") finalized = true;
      if (ev.type === "error") failed = true;
      continue;
    }
    if (ev.node in grouped) grouped[ev.node as StepKey].push(ev);
  }

  let activeKey: StepKey | null = null;
  if (!finalized) {
    for (let i = currentEvents.length - 1; i >= 0; i--) {
      const ev = currentEvents[i];
      if (ev?.node && ev.node !== "orchestrator" && (ev.node as StepKey) in grouped) {
        activeKey = ev.node as StepKey;
        break;
      }
    }
  }

  const order: StepKey[] = [
    "doc_parser",
    "risk_assessor",
    "guidelines_rag",
    "decision_draft",
    "critic",
  ];
  const activeIdx = activeKey ? order.indexOf(activeKey) : -1;
  const seenIdx = order.findIndex((k) => grouped[k].length > 0);

  const steps: StepState[] = STEPS.map((meta, i) => {
    const stepEvents = grouped[meta.key];
    const latest = stepEvents[stepEvents.length - 1];
    const stepErrored = stepEvents.some((e) => e.type === "error");
    let status: StepStatus = "pending";
    if (stepErrored) {
      status = "error";
    } else if (failed && stepEvents.length > 0) {
      status = "done";
    } else if (finalized) {
      status = stepEvents.length > 0 ? "done" : "pending";
    } else if (activeKey === meta.key) {
      status = "active";
    } else if (activeIdx >= 0 && i > activeIdx) {
      // graph looped back; later steps will re-run, so they're pending again
      status = "pending";
    } else if (stepEvents.length > 0 && (activeIdx < 0 || i < activeIdx)) {
      status = "done";
    } else if (seenIdx >= 0 && i < seenIdx) {
      status = "pending";
    }

    const hasIssues = meta.key === "critic" && Number(latest?.issue_count ?? 0) > 0;
    const reruns = Math.max(0, stepEvents.length - 1);
    const errorEvent = stepErrored ? stepEvents.find((e) => e.type === "error") : undefined;
    const errorMessage = errorEvent ? humanizeError(errorEvent.error) : null;

    return {
      key: meta.key,
      short: meta.short,
      label: meta.label,
      description: meta.description,
      status,
      summary: summarize(meta.key, latest),
      reruns,
      hasIssues,
      errorMessage,
      latest,
    };
  });

  return { steps, finalized, failed };
}
