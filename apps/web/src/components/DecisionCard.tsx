import type { DecisionPayload } from "@/lib/types";

type VerdictMeta = {
  label: string;
  chipBg: string;
  chipColor: string;
  ribbonBg: string;
  headline: string;
  whatItMeans: (loading: number) => string;
  numeralColor: string;
};

const VERDICT_META: Record<string, VerdictMeta> = {
  accept: {
    label: "Approved",
    chipBg: "var(--good)",
    chipColor: "white",
    ribbonBg: "color-mix(in oklch, var(--good) 8%, var(--paper))",
    headline: "We can offer you this coverage.",
    whatItMeans: () =>
      "Your application has been approved at the standard rate. No conditions to satisfy and nothing extra to do - your decision is ready.",
    numeralColor: "var(--good)",
  },
  accept_with_conditions: {
    label: "Approved with conditions",
    chipBg: "var(--warn)",
    chipColor: "white",
    ribbonBg: "color-mix(in oklch, var(--warn) 8%, var(--paper))",
    headline: "We can offer you coverage with a few conditions.",
    whatItMeans: (loading) =>
      loading > 0
        ? `Your premium will be ${loading.toFixed(0)}% higher than standard, and you'll need to satisfy the conditions listed below.`
        : "You're approved as long as you satisfy the conditions listed below.",
    numeralColor: "var(--warn)",
  },
  refer: {
    label: "Needs senior review",
    chipBg: "var(--ink)",
    chipColor: "var(--paper)",
    ribbonBg: "var(--paper-2)",
    headline: "A senior underwriter needs to take a closer look.",
    whatItMeans: () =>
      "Your case has signals our automated process can't decide on alone. A senior underwriter will follow up - usually with a request for more medical evidence.",
    numeralColor: "var(--ink)",
  },
  decline: {
    label: "Cannot offer",
    chipBg: "var(--bad)",
    chipColor: "white",
    ribbonBg: "color-mix(in oklch, var(--bad) 8%, var(--paper))",
    headline: "We can't offer this coverage at this tier.",
    whatItMeans: () =>
      "Based on the information provided, we aren't able to offer this coverage tier today. The detailed reasoning is below - a lower tier or a re-evaluation may still be possible.",
    numeralColor: "var(--bad)",
  },
};

function metaFor(verdict: string): VerdictMeta {
  return (
    VERDICT_META[verdict] ?? {
      label: verdict.replace(/_/g, " "),
      chipBg: "var(--ink)",
      chipColor: "var(--paper)",
      ribbonBg: "var(--paper-2)",
      headline: "Decision ready.",
      whatItMeans: () => "See the details below.",
      numeralColor: "var(--ink)",
    }
  );
}

export function DecisionCard({ decision }: { decision: DecisionPayload }) {
  const meta = metaFor(decision.verdict);
  const loading = decision.premium_loading_pct;

  return (
    <article className="overflow-hidden rounded border border-line bg-paper">
      <div className="px-7 py-7" style={{ background: meta.ribbonBg, borderBottom: "1px solid var(--line)" }}>
        <span
          className="chip"
          style={{
            background: meta.chipBg,
            color: meta.chipColor,
            borderColor: meta.chipBg,
          }}
        >
          {meta.label}
        </span>
        <h2 className="serif mt-4 mb-1.5 text-[26px] leading-[1.15] tracking-[-0.01em] sm:text-[28px]">
          {meta.headline}
        </h2>
        <p className="m-0 max-w-[540px] text-[14px] leading-[1.55] text-muted">
          {meta.whatItMeans(loading)}
        </p>
      </div>

      <div className="grid grid-cols-3 divide-x divide-line border-b border-line">
        <div className="px-5 py-4">
          <div className="field-label mb-1.5">Standard premium</div>
          <div className="serif text-[20px] leading-none text-ink">base rate</div>
        </div>
        <div className="px-5 py-4">
          <div className="field-label mb-1.5">Loading</div>
          <div
            className="serif tnum text-[20px] leading-none"
            style={{ color: loading > 0 ? "var(--warn)" : "var(--good)" }}
          >
            {loading > 0 ? `+${loading.toFixed(1)}%` : "no extra"}
          </div>
        </div>
        <div className="px-5 py-4">
          <div className="field-label mb-1.5">You will pay</div>
          <div className="serif tnum text-[20px] leading-none text-ink">
            {loading > 0 ? `${(100 + loading).toFixed(1)}% of base` : "base rate"}
          </div>
        </div>
      </div>

      <div className="px-7 py-6">
        {decision.conditions.length > 0 ? (
          <>
            <div className="field-label mb-2.5">Conditions</div>
            <ul className="m-0 list-none p-0">
              {decision.conditions.map((c, i) => (
                <li
                  key={i}
                  className="flex gap-3.5 py-3 text-[14px] leading-[1.55]"
                  style={{ borderTop: i === 0 ? "none" : "1px solid var(--line)" }}
                >
                  <span
                    className="serif tnum"
                    style={{ fontSize: 22, color: meta.numeralColor, minWidth: 24 }}
                  >
                    {i + 1}
                  </span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
            <div className="hr my-5" />
          </>
        ) : null}

        <div className="field-label">Reasoning</div>
        <p className="mt-2 text-[14px] leading-[1.6] text-ink-2">
          {decision.reasoning}
        </p>

        {decision.citations.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {decision.citations.map((c) => (
              <span key={c} className="chip mono" style={{ fontSize: 10 }}>
                {c}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </article>
  );
}
