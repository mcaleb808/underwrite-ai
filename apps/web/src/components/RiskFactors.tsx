import type { RiskFactor } from "@/lib/types";

const SOURCE_BADGES: Record<string, { label: string; className: string }> = {
  declared: {
    label: "From profile",
    className: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
  },
  parsed_medical: {
    label: "From documents",
    className: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  },
  district: {
    label: "Local data",
    className: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  },
  computed: {
    label: "Calculated",
    className: "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
  },
};

const FRIENDLY_NAMES: Record<string, string> = {
  age_band_18_30: "Age 18–30",
  age_band_31_45: "Age 31–45",
  age_band_46_55: "Age 46–55",
  age_band_56_65: "Age 56–65",
  age_band_66_70: "Age 66–70",
  bmi_underweight: "BMI · underweight",
  bmi_normal: "BMI · normal",
  bmi_overweight: "BMI · overweight",
  bmi_obese_1: "BMI · obese (class I)",
  bmi_obese_2: "BMI · obese (class II)",
  bmi_obese_3: "BMI · obese (class III)",
  htn_controlled: "Hypertension · controlled",
  htn_uncontrolled: "Hypertension · uncontrolled",
  dm_controlled: "Diabetes · controlled",
  dm_borderline: "Diabetes · borderline",
  dm_uncontrolled: "Diabetes · uncontrolled",
  cardiac_history: "Cardiac history",
  tobacco: "Tobacco use",
  alcohol_excess: "Alcohol above limit",
  high_risk_pregnancy: "High-risk pregnancy",
  district_endemic: "Local disease prevalence",
  occupation_class_II: "Job risk · manual / outdoor",
  occupation_class_III: "Job risk · hazardous",
  comorbid_htn_dm: "Hypertension + diabetes together",
};

function friendlyName(name: string): string {
  if (FRIENDLY_NAMES[name]) return FRIENDLY_NAMES[name];
  // fallback: convert "snake_case" to "Snake case"
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/Bmi/g, "BMI")
    .replace(/Htn/g, "Hypertension")
    .replace(/Dm/g, "Diabetes");
}

function bandFor(score: number): { label: string; className: string } {
  if (score <= 25) return { label: "Low", className: "text-emerald-600 dark:text-emerald-400" };
  if (score <= 50) return { label: "Moderate", className: "text-amber-600 dark:text-amber-400" };
  if (score <= 75) return { label: "High", className: "text-orange-600 dark:text-orange-400" };
  return { label: "Very high", className: "text-red-600 dark:text-red-400" };
}

export function RiskFactors({ factors }: { factors: RiskFactor[] }) {
  if (factors.length === 0) return null;
  const total = factors.reduce((acc, f) => acc + f.contribution, 0);
  const maxContribution = Math.max(1, ...factors.map((f) => f.contribution));
  const band = bandFor(total);

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
      <header className="mb-4 flex items-end justify-between gap-3">
        <div>
          <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            What shaped your risk
          </h2>
          <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">
            Each item below contributes points to the total risk score.
          </p>
        </div>
        <div className="text-right">
          <div className={`text-xl font-semibold tabular-nums ${band.className}`}>
            {total.toFixed(1)}
          </div>
          <div className={`text-[10px] font-medium uppercase tracking-wide ${band.className}`}>
            {band.label}
          </div>
        </div>
      </header>

      <ul className="space-y-2">
        {factors.map((f, i) => {
          const source =
            SOURCE_BADGES[f.source] ??
            ({ label: "Calculated", className: "bg-zinc-100 text-zinc-600" } as const);
          const widthPct = Math.max(2, (f.contribution / maxContribution) * 100);
          const isZero = f.contribution === 0;
          return (
            <li
              key={i}
              className="rounded-md border border-zinc-100 bg-zinc-50/50 px-3 py-2 dark:border-zinc-800 dark:bg-zinc-900/40"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2">
                  <span className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                    {friendlyName(f.name)}
                  </span>
                  <span
                    className={`shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-medium ${source.className}`}
                  >
                    {source.label}
                  </span>
                </div>
                <span
                  className={`shrink-0 text-sm font-semibold tabular-nums ${
                    isZero ? "text-zinc-400" : "text-zinc-900 dark:text-zinc-50"
                  }`}
                >
                  {isZero ? "—" : `+${f.contribution.toFixed(1)}`}
                </span>
              </div>
              {!isZero ? (
                <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-zinc-200/70 dark:bg-zinc-800">
                  <div
                    className="h-full rounded-full bg-zinc-700 dark:bg-zinc-300"
                    style={{ width: `${widthPct}%` }}
                  />
                </div>
              ) : null}
              {f.evidence ? (
                <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{f.evidence}</p>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
