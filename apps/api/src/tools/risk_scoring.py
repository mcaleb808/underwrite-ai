"""Deterministic underwriting risk score per UW-010..UW-130.

Score is additive across domains and capped at 100. Each domain contributes a
RiskFactor with `value` (the raw points before weight), `weight` (always 1.0
in this v1 — kept for forward compat with calibrated weights), `contribution`
(value * weight), and an `evidence` string the critic can audit.

Pregnancy-only and Ubudehe categories are handled per UW-090/UW-100 — they
never produce adverse loading.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.schemas.applicant import ApplicantProfile
from src.schemas.decision import RiskFactor
from src.schemas.medical import ParsedMedicalRecord
from src.tools.age_band import classify_age_band, compute_age
from src.tools.bmi import classify_bmi, compute_bmi
from src.tools.district_prevalence import endemic_loading

RiskBand = Literal["low", "moderate", "high", "very_high"]

_AGE_POINTS: dict[str, float] = {
    "18_30": 0,
    "31_45": 15,
    "46_55": 30,
    "56_65": 45,
    "66_70": 55,
    "out_of_range": 0,
}

_BMI_POINTS: dict[str, float] = {
    "underweight": 5,
    "normal": 0,
    "overweight": 10,
    "obese_1": 22,
    "obese_2": 40,
    "obese_3": 60,
}

_HTN_TERMS = ("hypertension", "htn", "high blood pressure")
_DM_TERMS = ("diabetes", "t2dm", "type 2 diabetes", "type 1 diabetes", "t1dm")
_CARDIAC_TERMS = ("myocardial infarction", "mi", "coronary", "cad", "stroke", "angina")
_PREGNANCY_TERMS = ("pregnancy", "pregnant", "gravid")
_HIGH_RISK_PREGNANCY_TERMS = (
    "gestational diabetes",
    "pre-eclampsia",
    "preeclampsia",
    "multiple gestation",
)

_AGE_BAND_LABELS: dict[str, str] = {
    "18_30": "18-30 (young adult)",
    "31_45": "31-45 (working age)",
    "46_55": "46-55 (mid-life)",
    "56_65": "56-65 (pre-retirement)",
    "66_70": "66-70 (senior)",
    "out_of_range": "outside the underwriting range",
}

_BMI_LABELS: dict[str, str] = {
    "underweight": "underweight",
    "normal": "normal weight range",
    "overweight": "above the healthy range",
    "obese_1": "obese class I",
    "obese_2": "obese class II",
    "obese_3": "obese class III",
}


@dataclass
class RiskAssessment:
    score: float
    band: RiskBand
    factors: list[RiskFactor]


def _has_term(history: list[str], terms: tuple[str, ...]) -> bool:
    haystack = " ".join(history).lower()
    return any(term in haystack for term in terms)


def _classify_htn(profile: ApplicantProfile) -> Literal["none", "controlled", "uncontrolled"]:
    sbp = profile.vitals.sbp
    dbp = profile.vitals.dbp
    if sbp is not None and dbp is not None and (sbp >= 140 or dbp >= 90):
        return "uncontrolled"
    if _has_term(profile.declared_history, _HTN_TERMS):
        return "controlled"
    return "none"


def _classify_dm(
    profile: ApplicantProfile,
) -> Literal["none", "controlled", "borderline", "uncontrolled"]:
    # Default to controlled when only declared (no labs yet); doc_parser can
    # later refine via HbA1c. GDM is handled in pregnancy, not here.
    if _has_term(profile.declared_history, ("gestational diabetes",)):
        return "none"
    if _has_term(profile.declared_history, _DM_TERMS):
        return "controlled"
    return "none"


def _band_for(score: float) -> RiskBand:
    if score <= 25:
        return "low"
    if score <= 50:
        return "moderate"
    if score <= 75:
        return "high"
    return "very_high"


def assess_risk(
    profile: ApplicantProfile,
    parsed: list[ParsedMedicalRecord] | None = None,
) -> RiskAssessment:
    """Compute deterministic risk score (0-100) and contributing factors."""
    factors: list[RiskFactor] = []

    age = compute_age(profile.demographics.dob)
    age_band = classify_age_band(age)
    age_points = _AGE_POINTS[age_band]
    factors.append(
        RiskFactor(
            name=f"age_band_{age_band}",
            weight=1.0,
            value=age_points,
            contribution=age_points,
            source="declared",
            evidence=f"Age {age} — {_AGE_BAND_LABELS.get(age_band, age_band)}",
        )
    )

    bmi = compute_bmi(profile.vitals.height_cm, profile.vitals.weight_kg)
    bmi_class = classify_bmi(bmi)
    bmi_points = _BMI_POINTS[bmi_class]
    factors.append(
        RiskFactor(
            name=f"bmi_{bmi_class}",
            weight=1.0,
            value=bmi_points,
            contribution=bmi_points,
            source="declared",
            evidence=f"BMI {bmi:.1f} — {_BMI_LABELS.get(bmi_class, bmi_class)}",
        )
    )

    htn = _classify_htn(profile)
    htn_points = {"none": 0.0, "controlled": 15.0, "uncontrolled": 35.0}[htn]
    if htn != "none":
        sbp = profile.vitals.sbp
        dbp = profile.vitals.dbp
        bp_part = f"Blood pressure {sbp}/{dbp} mmHg" if sbp and dbp else "Blood pressure"
        status_part = (
            "controlled with medication" if htn == "controlled" else "currently uncontrolled"
        )
        factors.append(
            RiskFactor(
                name=f"htn_{htn}",
                weight=1.0,
                value=htn_points,
                contribution=htn_points,
                source="declared",
                evidence=f"{bp_part} — {status_part}",
            )
        )

    dm = _classify_dm(profile)
    dm_points = {"none": 0.0, "controlled": 25.0, "borderline": 40.0, "uncontrolled": 60.0}[dm]
    if dm != "none":
        dm_status = {
            "controlled": "treated and stable (no recent HbA1c on file)",
            "borderline": "borderline control",
            "uncontrolled": "uncontrolled",
        }[dm]
        factors.append(
            RiskFactor(
                name=f"dm_{dm}",
                weight=1.0,
                value=dm_points,
                contribution=dm_points,
                source="declared",
                evidence=f"Diabetes — {dm_status}",
            )
        )

    cardiac_points = 30.0 if _has_term(profile.declared_history, _CARDIAC_TERMS) else 0.0
    if cardiac_points:
        factors.append(
            RiskFactor(
                name="cardiac_history",
                weight=1.0,
                value=cardiac_points,
                contribution=cardiac_points,
                source="declared",
                evidence="Reported a past cardiac event or condition",
            )
        )

    tobacco_points = 15.0 if profile.lifestyle.tobacco != "none" else 0.0
    if tobacco_points:
        tobacco_label = {
            "occasional": "Smokes occasionally",
            "daily": "Smokes daily",
        }.get(profile.lifestyle.tobacco, "Tobacco use reported")
        factors.append(
            RiskFactor(
                name="tobacco",
                weight=1.0,
                value=tobacco_points,
                contribution=tobacco_points,
                source="declared",
                evidence=tobacco_label,
            )
        )

    alcohol_points = 15.0 if profile.lifestyle.alcohol_units_per_week > 21 else 0.0
    if alcohol_points:
        factors.append(
            RiskFactor(
                name="alcohol_excess",
                weight=1.0,
                value=alcohol_points,
                contribution=alcohol_points,
                source="declared",
                evidence=(
                    f"{profile.lifestyle.alcohol_units_per_week} drinks per week"
                    " (above the 21-unit limit)"
                ),
            )
        )

    if _has_term(profile.declared_history, _PREGNANCY_TERMS) and _has_term(
        profile.declared_history, _HIGH_RISK_PREGNANCY_TERMS
    ):
        pregnancy_points = 25.0
        factors.append(
            RiskFactor(
                name="high_risk_pregnancy",
                weight=1.0,
                value=pregnancy_points,
                contribution=pregnancy_points,
                source="declared",
                evidence="Pregnancy with high-risk markers reported (UW-100)",
            )
        )

    district_points = endemic_loading(profile.demographics.district)
    if district_points:
        factors.append(
            RiskFactor(
                name="district_endemic",
                weight=1.0,
                value=district_points,
                contribution=district_points,
                source="district",
                evidence=(
                    f"{profile.demographics.district} has higher malaria prevalence"
                    " (UW-070 endemic loading)"
                ),
            )
        )

    occupation_points = {"I": 0.0, "II": 8.0, "III": 22.0}[profile.occupation.class_]
    if occupation_points:
        class_descriptor = {
            "II": "manual / outdoor work",
            "III": "hazardous work",
        }.get(profile.occupation.class_, "")
        factors.append(
            RiskFactor(
                name=f"occupation_class_{profile.occupation.class_}",
                weight=1.0,
                value=occupation_points,
                contribution=occupation_points,
                source="declared",
                evidence=(
                    f"{profile.occupation.title} — {class_descriptor}"
                    if class_descriptor
                    else profile.occupation.title
                ),
            )
        )

    comorbid_points = 10.0 if htn != "none" and dm != "none" else 0.0
    if comorbid_points:
        factors.append(
            RiskFactor(
                name="comorbid_htn_dm",
                weight=1.0,
                value=comorbid_points,
                contribution=comorbid_points,
                source="computed",
                evidence="Hypertension and diabetes occurring together (UW-030)",
            )
        )

    raw_score = sum(f.contribution for f in factors)
    score = min(100.0, round(raw_score, 2))
    return RiskAssessment(score=score, band=_band_for(score), factors=factors)
