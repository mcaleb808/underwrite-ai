import type { DecisionPayload } from "@/lib/types";

const VERDICT_STYLES: Record<string, string> = {
  accept: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  accept_with_conditions:
    "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  refer: "bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300",
  decline: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
};

export function DecisionCard({ decision }: { decision: DecisionPayload }) {
  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
      <header className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          Decision
        </h2>
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-medium ${
            VERDICT_STYLES[decision.verdict] ?? "bg-zinc-100 text-zinc-700"
          }`}
        >
          {decision.verdict.replace(/_/g, " ")}
        </span>
      </header>

      <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
        <div>
          <dt className="text-zinc-500 dark:text-zinc-400">Premium loading</dt>
          <dd className="font-medium text-zinc-900 dark:text-zinc-50">
            +{decision.premium_loading_pct.toFixed(1)}%
          </dd>
        </div>
        <div>
          <dt className="text-zinc-500 dark:text-zinc-400">Citations</dt>
          <dd className="font-medium text-zinc-900 dark:text-zinc-50">
            {decision.citations.join(", ") || "—"}
          </dd>
        </div>
      </dl>

      {decision.conditions.length > 0 ? (
        <div className="mt-4">
          <h3 className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Conditions
          </h3>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-zinc-700 dark:text-zinc-300">
            {decision.conditions.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-4">
        <h3 className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          Reasoning
        </h3>
        <p className="mt-1 whitespace-pre-line text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          {decision.reasoning}
        </p>
      </div>
    </section>
  );
}
