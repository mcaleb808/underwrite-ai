# UnderwriteAI Rwandan Underwriting Manual v1.0

> **SYNTHETIC DATA** - This document is entirely fictional, created for demonstration
> purposes only. It does not represent real underwriting policy or medical guidance.

## UW-001 Eligibility and residency

- Age at entry 18–70; renewal up to 75.
- Must be Rwandan national or legal resident with a valid NID (16 digits).
- Proof of CBHI (Mutuelle de Santé) or private scheme enrollment required for sum insured > 5,000,000 RWF.
- Applicants under 18 or over 70 are outside the scope of this product.

## UW-010 Age-band base risk factor

Age at application determines the base risk factor applied to the premium.

| Band  | Factor |
|-------|--------|
| 18–30 | 1.00   |
| 31–45 | 1.15   |
| 46–55 | 1.35   |
| 56–65 | 1.70   |
| 66–70 | 2.20   |

Age is computed from the date of birth on the NID. Fractional years are rounded down.

## UW-020 BMI classification and loading

Body mass index is calculated as weight (kg) / height (m)². The classification drives premium loading.

| BMI       | Class        | Loading                       |
|-----------|--------------|-------------------------------|
| < 18.5    | Underweight  | +10%, require nutrition note  |
| 18.5–24.9 | Normal       | 0%                            |
| 25–29.9   | Overweight   | +10%                          |
| 30–34.9   | Obese I      | +25%                          |
| 35–39.9   | Obese II     | +50%                          |
| ≥ 40      | Obese III    | Refer to senior underwriter   |

## UW-030 Hypertension

- **Controlled** (SBP < 140, DBP < 90 on medication, stable ≥ 12 months): standard rate + 15% loading.
- **Uncontrolled** or newly diagnosed (< 6 months): refer to senior underwriter.
- Evidence required: two consecutive BP readings at least 4 weeks apart, plus current medication list.
- Co-morbidity with diabetes increases loading by an additional 10% (see UW-040).

## UW-040 Diabetes mellitus

- **T2DM, HbA1c < 7.0**, no complications: +25% loading.
- **HbA1c 7.0–8.5**: refer with endocrinologist report.
- **HbA1c > 8.5** or any end-organ complication (retinopathy, nephropathy, neuropathy): decline at this tier; offer lower-tier product.
- T1DM: refer regardless of control level.
- Evidence required: HbA1c within last 3 months, fasting blood sugar, renal function panel.

## UW-050 HIV serostatus

- **Positive with documented ART adherence ≥ 6 months and undetectable viral load**: accept at sub-standard tier SS-2, +40% loading. This is consistent with Rwandan life-insurance precedents that permit cover for well-controlled HIV-positive applicants.
- **Positive, non-adherent or missing viral load results**: refer.
- **Negative**: no loading from this factor.
- Evidence required: CD4 count, viral load (within 3 months), ART regimen documentation.

## UW-060 Tuberculosis history

- **Treated and cleared > 24 months ago**: standard rate, no loading.
- **Active TB or within 24 months of treatment completion**: postpone application until 24-month clearance period is met.
- Evidence required: treatment completion certificate, chest X-ray showing no active disease.

## UW-070 Malaria and endemic exposure (district-adjusted)

- Apply district-level endemic loading from `districts.json`, capped at +10%.
- Malaria prevalence in Rwanda varies substantially by district (e.g. Kigali districts vs eastern border districts). The cap prevents applicants from being unfairly penalized for their place of residence beyond a reasonable range.
- This loading is purely actuarial and must not be conflated with socio-economic status.

## UW-080 Occupation risk class

Occupational risk is classified into three tiers based on physical hazard and environmental exposure.

| Class | Examples                                               | Loading |
|-------|--------------------------------------------------------|---------|
| I     | Office worker, teacher, trader, healthcare admin       | 0%      |
| II    | Farmer, construction worker, nurse                     | +10%    |
| III   | Mining, commercial motorcycle (abamotari), pesticide handler | +30% |

## UW-090 Ubudehe category - equity protection

- Ubudehe 1–2: flag for premium subsidy eligibility; **no adverse loading** on socio-economic grounds.
- Ubudehe 3–4: standard.
- Ubudehe **cannot** be the sole or contributing basis for decline or for any adverse risk adjustment. This is a hard constraint enforced by UW-140.
- The Ubudehe category may appear in the decision context for subsidy-flagging purposes only.

## UW-100 Pregnancy

- **Normal pregnancy** is not an adverse risk factor. Accept at standard rate; maternity rider assessed separately.
- **High-risk pregnancy** (pre-eclampsia history, gestational diabetes, multiple gestation): refer to senior underwriter.
- Pregnancy status alone must never result in decline or adverse loading.

## UW-110 Lifestyle - tobacco and alcohol

- **Tobacco (any form)**: +20% loading. If concurrent with hypertension (UW-030) or HIV (UW-050), refer instead of loading.
- **Alcohol > 21 units/week** (self-reported or documented): refer.
- **Alcohol ≤ 21 units/week**: no loading.
- Self-reported lifestyle factors should be cross-checked against medical notes where available.

## UW-120 Medical evidence requirements by sum insured

The level of medical evidence required scales with the sum insured.

| Sum insured (RWF) | Evidence required                                    |
|--------------------|------------------------------------------------------|
| ≤ 2M               | Declaration only                                     |
| 2M–10M             | Basic labs + BP + BMI                                |
| 10M–50M            | + ECG, FBS/HbA1c, lipid panel, HIV test              |
| > 50M              | + Treadmill stress test, specialist report            |

## UW-130 Risk score to verdict mapping

The weighted risk score maps to a verdict category. Hard-rule overrides (UW-040, UW-050, UW-060) take precedence over the score-based mapping.

| Score  | Verdict                |
|--------|------------------------|
| 0–25   | Accept                 |
| 26–50  | Accept with conditions |
| 51–75  | Refer                  |
| 76–100 | Decline                |

## UW-140 Mandatory critic checks (fairness and consistency)

Before any decision is finalized, the following checks must pass:

**(a)** No adverse decision cites Ubudehe category, CBHI (Mutuelle) status, or district-of-residence as a contributing factor. Using Ubudehe as a reason for decline is a hard fail.

**(b)** Every condition cited in the reasoning has supporting evidence in the parsed medical record or declared history. Unsupported claims must be flagged.

**(c)** Endemic loadings are capped per UW-070 at +10%. Any violation must be corrected.

**(d)** Loadings sum correctly; no double-counting of the same condition across multiple risk factors.

**(e)** Any hard-rule verdict (UW-040 HbA1c > 8.5, UW-060 active TB, UW-050 non-adherent HIV) is honored regardless of the score-based mapping.
