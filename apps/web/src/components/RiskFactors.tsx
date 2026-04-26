import type { RiskFactor } from "@/lib/types";

const SOURCE_LABEL: Record<string, string> = {
  declared: "from profile",
  parsed_medical: "from documents",
  district: "local data",
  computed: "calculated",
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
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/Bmi/g, "BMI")
    .replace(/Htn/g, "Hypertension")
    .replace(/Dm/g, "Diabetes");
}

export function RiskFactors({ factors }: { factors: RiskFactor[] }) {
  if (factors.length === 0) return null;
  const max = Math.max(1, ...factors.map((f) => f.contribution));
  const top = factors.slice(0, 8);

  return (
    <div>
      <div className="field-label">What shaped the score</div>
      <ul className="m-0 mt-3 list-none p-0">
        {top.map((f, i) => {
          const pct = Math.max(2, (f.contribution / max) * 100);
          const isZero = f.contribution === 0;
          return (
            <li
              key={i}
              className="py-3"
              style={{ borderBottom: i < top.length - 1 ? "1px solid var(--line)" : "none" }}
            >
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-[13px] font-medium">{friendlyName(f.name)}</span>
                <span
                  className="serif tnum text-[16px]"
                  style={{ color: isZero ? "var(--muted-2)" : "var(--ink)" }}
                >
                  {isZero ? "—" : `+${f.contribution.toFixed(1)}`}
                </span>
              </div>
              <div className="mono mt-0.5 text-[10px] text-muted">
                {SOURCE_LABEL[f.source] ?? "calculated"}
              </div>
              {!isZero ? (
                <div className="mt-1.5 h-[2px] w-full bg-line">
                  <div className="h-full bg-ink" style={{ width: `${pct}%` }} />
                </div>
              ) : null}
              {f.evidence ? (
                <p className="mt-1 text-[11px] text-muted">{f.evidence}</p>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
