import type { RiskFactor } from "@/lib/types";

const SOURCE_STYLES: Record<string, string> = {
  declared: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
  parsed_medical: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  district: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  computed: "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
};

export function RiskFactors({ factors }: { factors: RiskFactor[] }) {
  if (factors.length === 0) return null;
  const total = factors.reduce((acc, f) => acc + f.contribution, 0);

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          Risk factors
        </h2>
        <span className="text-xs text-zinc-500">
          total contribution: {total.toFixed(1)}
        </span>
      </header>
      <ul className="space-y-1.5">
        {factors.map((f, i) => (
          <li
            key={i}
            className="flex items-start justify-between gap-3 rounded-md border border-zinc-100 px-3 py-2 text-sm dark:border-zinc-800"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-zinc-700 dark:text-zinc-300">
                  {f.name}
                </span>
                <span
                  className={`rounded-full px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${
                    SOURCE_STYLES[f.source] ?? "bg-zinc-100 text-zinc-600"
                  }`}
                >
                  {f.source}
                </span>
              </div>
              {f.evidence ? (
                <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">
                  {f.evidence}
                </p>
              ) : null}
            </div>
            <span
              className={`shrink-0 font-mono text-sm tabular-nums ${
                f.contribution > 0
                  ? "text-zinc-900 dark:text-zinc-50"
                  : "text-zinc-400"
              }`}
            >
              +{f.contribution.toFixed(1)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
