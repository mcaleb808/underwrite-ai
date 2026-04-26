"""Unit tests for deterministic underwriting tools - no LLM calls."""

import json
from datetime import date
from pathlib import Path

import pytest

from src.schemas.applicant import ApplicantProfile
from src.tools.age_band import classify_age_band, compute_age
from src.tools.bmi import classify_bmi, compute_bmi
from src.tools.district_prevalence import endemic_loading, lookup_district
from src.tools.risk_scoring import assess_risk

APPLICANTS_DIR = Path(__file__).resolve().parent.parent / "src" / "data" / "applicants"


def _load(applicant_id: str) -> ApplicantProfile:
    return ApplicantProfile.model_validate_json(
        (APPLICANTS_DIR / f"{applicant_id}.json").read_text()
    )


def test_compute_bmi() -> None:
    assert compute_bmi(170, 70) == pytest.approx(24.22, abs=0.01)
    assert compute_bmi(165, 60) == pytest.approx(22.04, abs=0.01)


@pytest.mark.parametrize(
    "bmi, cls",
    [
        (17.0, "underweight"),
        (22.0, "normal"),
        (27.5, "overweight"),
        (32.0, "obese_1"),
        (37.0, "obese_2"),
        (41.0, "obese_3"),
    ],
)
def test_classify_bmi(bmi: float, cls: str) -> None:
    assert classify_bmi(bmi) == cls


def test_compute_age_handles_pre_birthday() -> None:
    # On 2026-01-01 someone born 1990-06-01 is still 35.
    assert compute_age(date(1990, 6, 1), on=date(2026, 1, 1)) == 35
    assert compute_age(date(1990, 6, 1), on=date(2026, 6, 1)) == 36


@pytest.mark.parametrize(
    "age, band",
    [
        (25, "18_30"),
        (40, "31_45"),
        (50, "46_55"),
        (60, "56_65"),
        (68, "66_70"),
        (75, "out_of_range"),
        (17, "out_of_range"),
    ],
)
def test_classify_age_band(age: int, band: str) -> None:
    assert classify_age_band(age) == band


def test_district_lookup_known_and_unknown() -> None:
    nyarugenge = lookup_district("Nyarugenge")
    assert nyarugenge is not None
    assert nyarugenge["province"] == "Kigali"
    assert lookup_district("Atlantis") is None


def test_endemic_loading_capped_at_ten() -> None:
    # Nyagatare has malaria_per_1000 = 50 -> raw 10.0 -> capped at 10.
    assert endemic_loading("Nyagatare") == 10.0
    # Nyarugenge low malaria.
    assert endemic_loading("Nyarugenge") == pytest.approx(1.0, abs=0.01)
    assert endemic_loading("Atlantis") == 0.0


# Expected scores derived from manual walk-through of UW-010..UW-130.
# DoD: each persona within +/-5 of the expected number.
EXPECTED_SCORES: list[tuple[str, float]] = [
    ("alice-kigali-clean", 1.0),
    ("jean-nyanza-controlled-htn", 43.6),
    ("marie-rubavu-diabetic", 100.0),
    ("emmanuel-gakenke-cardiac", 100.0),
    ("claudine-nyagatare-pregnant", 58.0),
]


@pytest.mark.parametrize("applicant_id, expected", EXPECTED_SCORES)
def test_persona_risk_score_within_tolerance(applicant_id: str, expected: float) -> None:
    profile = _load(applicant_id)
    result = assess_risk(profile)
    assert abs(result.score - expected) <= 5, (
        f"{applicant_id}: got {result.score}, expected {expected} +/- 5"
    )


def test_band_mapping_matches_uw_130() -> None:
    profile_low = _load("alice-kigali-clean")
    assert assess_risk(profile_low).band == "low"

    profile_high = _load("emmanuel-gakenke-cardiac")
    assert assess_risk(profile_high).band == "very_high"


def test_no_factor_uses_ubudehe_or_cbhi() -> None:
    """UW-090: socio-economic markers must never appear as risk factors."""
    for applicant_id, _ in EXPECTED_SCORES:
        profile = _load(applicant_id)
        result = assess_risk(profile)
        for factor in result.factors:
            assert "ubudehe" not in factor.name.lower()
            assert "cbhi" not in factor.name.lower()
            evidence = (factor.evidence or "").lower()
            assert "ubudehe" not in evidence
            assert "cbhi" not in evidence


def test_applicants_dir_has_five_personas() -> None:
    """Sanity: the test list above covers everything in the applicants dir."""
    files = sorted(p.stem for p in APPLICANTS_DIR.glob("*.json"))
    assert files == sorted(a for a, _ in EXPECTED_SCORES)
    # Also verify each JSON parses cleanly.
    for f in files:
        json.loads((APPLICANTS_DIR / f"{f}.json").read_text())
