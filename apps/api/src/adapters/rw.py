"""Rwanda region adapter — fairness checks and country-specific rules."""

import re

from src.schemas.applicant import ApplicantProfile
from src.schemas.decision import DecisionDraft, RiskFactor

# terms that must never appear as reasons in adverse decisions (UW-090, UW-140)
_BIAS_TERMS = re.compile(
    r"\b(ubudehe|mutuelle|cbhi|mutuelle de sant[eé])\b",
    re.IGNORECASE,
)


class RwandaAdapter:
    country_code: str = "RW"

    def extra_risk_factors(self, applicant: ApplicantProfile) -> list[RiskFactor]:
        """Return context-only factors (contribution=0) for display purposes."""
        factors: list[RiskFactor] = []

        # ubudehe is shown for subsidy flagging but never contributes to score
        factors.append(
            RiskFactor(
                name=f"ubudehe_category_{applicant.demographics.ubudehe_category}",
                weight=0.0,
                value=0.0,
                contribution=0.0,
                source="declared",
                evidence=(
                    f"Ubudehe {applicant.demographics.ubudehe_category} (context only, no loading)"
                ),
            )
        )

        # cbhi status shown for context
        factors.append(
            RiskFactor(
                name=f"cbhi_{applicant.demographics.cbhi_status}",
                weight=0.0,
                value=0.0,
                contribution=0.0,
                source="declared",
                evidence=f"CBHI: {applicant.demographics.cbhi_status} (context only)",
            )
        )

        return factors

    def fairness_checks(self, draft: DecisionDraft, applicant: ApplicantProfile) -> list[str]:
        """Deterministic regex scan for bias terms in adverse decisions.

        This is a belt-and-braces backstop — the LLM critic may miss bias,
        but the regex cannot.
        """
        issues: list[str] = []

        if draft.verdict in ("refer", "decline"):
            # scan reasoning for protected terms
            matches = _BIAS_TERMS.findall(draft.reasoning)
            if matches:
                issues.append(
                    f"UW-140(a) violation: adverse decision reasoning mentions "
                    f"protected terms: {', '.join(set(matches))}"
                )

            # scan conditions for protected terms
            for condition in draft.conditions:
                matches = _BIAS_TERMS.findall(condition)
                if matches:
                    issues.append(
                        f"UW-140(a) violation: condition mentions protected "
                        f"terms: {', '.join(set(matches))}"
                    )

            # check if district is cited as an adverse factor
            district = applicant.demographics.district.lower()
            if district in draft.reasoning.lower() and "endemic" not in draft.reasoning.lower():
                issues.append(
                    f"UW-140(a) violation: district '{applicant.demographics.district}' "
                    f"cited in reasoning without endemic context"
                )

        return issues

    def evidence_threshold_tier(self, sum_insured_rwf: int) -> str:
        """Map sum insured to evidence tier per UW-120."""
        if sum_insured_rwf <= 2_000_000:
            return "T1"
        if sum_insured_rwf <= 10_000_000:
            return "T2"
        if sum_insured_rwf <= 50_000_000:
            return "T3"
        return "T4"


rw_adapter = RwandaAdapter()
