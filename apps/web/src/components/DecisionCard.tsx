"use client";

import { useState } from "react";

import type { DecisionPayload } from "@/lib/types";

type VerdictMeta = {
  label: string;
  badgeBg: string;
  borderTone: string;
  ribbonBg: string;
  headline: string;
  whatItMeans: (loading: number) => string;
};

const VERDICT_META: Record<string, VerdictMeta> = {
  accept: {
    label: "Approved",
    badgeBg: "bg-emerald-500 text-white",
    borderTone: "border-emerald-200 dark:border-emerald-900",
    ribbonBg: "bg-emerald-50 dark:bg-emerald-950/40",
    headline: "We can offer you this coverage.",
    whatItMeans: () =>
      "Your application has been approved at the standard rate. No conditions to satisfy and nothing extra to do — your decision is ready.",
  },
  accept_with_conditions: {
    label: "Approved with conditions",
    badgeBg: "bg-amber-500 text-white",
    borderTone: "border-amber-200 dark:border-amber-900",
    ribbonBg: "bg-amber-50 dark:bg-amber-950/40",
    headline: "We can offer you coverage with a few conditions.",
    whatItMeans: (loading) =>
      loading > 0
        ? `Your premium will be ${loading.toFixed(0)}% higher than standard, and you'll need to satisfy the conditions listed below.`
        : "You're approved as long as you satisfy the conditions listed below.",
  },
  refer: {
    label: "Needs senior review",
    badgeBg: "bg-orange-500 text-white",
    borderTone: "border-orange-200 dark:border-orange-900",
    ribbonBg: "bg-orange-50 dark:bg-orange-950/40",
    headline: "A senior underwriter needs to take a closer look.",
    whatItMeans: () =>
      "Your case has signals our automated process can't decide on alone. A senior underwriter will follow up — usually with a request for more medical evidence.",
  },
  decline: {
    label: "Cannot offer",
    badgeBg: "bg-red-500 text-white",
    borderTone: "border-red-200 dark:border-red-900",
    ribbonBg: "bg-red-50 dark:bg-red-950/40",
    headline: "We can't offer this coverage at this tier.",
    whatItMeans: () =>
      "Based on the information provided, we aren't able to offer this coverage tier today. The detailed reasoning is below — a lower tier or a re-evaluation may still be possible.",
  },
};

function metaFor(verdict: string): VerdictMeta {
  return (
    VERDICT_META[verdict] ?? {
      label: verdict.replace(/_/g, " "),
      badgeBg: "bg-zinc-500 text-white",
      borderTone: "border-zinc-200 dark:border-zinc-800",
      ribbonBg: "bg-zinc-50 dark:bg-zinc-900",
      headline: "Decision ready.",
      whatItMeans: () => "See the details below.",
    }
  );
}

export function DecisionCard({ decision }: { decision: DecisionPayload }) {
  const meta = metaFor(decision.verdict);
  const loading = decision.premium_loading_pct;
  const [showReasoning, setShowReasoning] = useState(false);

  return (
    <section
      className={`overflow-hidden rounded-xl border-2 ${meta.borderTone} bg-white dark:bg-zinc-950`}
    >
      {/* Headline ribbon */}
      <div className={`px-6 py-5 ${meta.ribbonBg}`}>
        <div className="flex items-center gap-3">
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${meta.badgeBg}`}
          >
            {meta.label}
          </span>
          <span className="text-xs uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Decision
          </span>
        </div>
        <h2 className="mt-3 text-lg font-semibold leading-snug text-zinc-900 dark:text-zinc-50">
          {meta.headline}
        </h2>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          {meta.whatItMeans(loading)}
        </p>
      </div>

      <div className="space-y-6 px-6 py-5">
        {/* Premium impact */}
        <div className="flex items-stretch divide-x divide-zinc-200 overflow-hidden rounded-lg border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
          <div className="flex-1 px-4 py-3">
            <div className="text-[10px] font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              Standard premium
            </div>
            <div className="mt-1 text-base font-semibold text-zinc-700 dark:text-zinc-200">
              base rate
            </div>
          </div>
          <div className="flex-1 px-4 py-3">
            <div className="text-[10px] font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              Loading
            </div>
            <div
              className={`mt-1 text-base font-semibold tabular-nums ${
                loading > 0 ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400"
              }`}
            >
              {loading > 0 ? `+${loading.toFixed(1)}%` : "no extra"}
            </div>
          </div>
          <div className="flex-1 px-4 py-3">
            <div className="text-[10px] font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              You will pay
            </div>
            <div className="mt-1 text-base font-semibold text-zinc-900 dark:text-zinc-50">
              {loading > 0 ? `${(100 + loading).toFixed(1)}% of base` : "base rate"}
            </div>
          </div>
        </div>

        {/* Conditions */}
        {decision.conditions.length > 0 ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50/60 px-4 py-3 dark:border-amber-900 dark:bg-amber-950/30">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-300">
              Conditions you&apos;ll need to satisfy
            </h3>
            <ul className="mt-2 space-y-1.5 text-sm text-zinc-800 dark:text-zinc-200">
              {decision.conditions.map((c, i) => (
                <li key={i} className="flex gap-2">
                  <span aria-hidden className="mt-1 shrink-0 text-amber-500">
                    •
                  </span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {/* Reasoning (collapsible) */}
        <div>
          <button
            type="button"
            onClick={() => setShowReasoning((v) => !v)}
            className="flex w-full items-center justify-between text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
            aria-expanded={showReasoning}
          >
            <span>Detailed reasoning</span>
            <span className="text-base font-normal">{showReasoning ? "−" : "+"}</span>
          </button>
          {showReasoning ? (
            <p className="mt-2 whitespace-pre-line rounded-md bg-zinc-50 px-3 py-2 text-sm leading-relaxed text-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
              {decision.reasoning}
            </p>
          ) : (
            <p className="mt-2 text-xs text-zinc-400 dark:text-zinc-500">
              The full underwriter-style explanation is hidden by default — open it to see the
              rule-by-rule analysis.
            </p>
          )}
        </div>

        {/* Rules applied */}
        {decision.citations.length > 0 ? (
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              Rules applied
            </h3>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {decision.citations.map((rule) => (
                <span
                  key={rule}
                  className="rounded-md border border-zinc-200 bg-white px-2 py-0.5 font-mono text-[11px] text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
                >
                  {rule}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
