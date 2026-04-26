"""Region adapters - protocol for country-specific underwriting logic."""

from typing import Protocol, runtime_checkable

from src.schemas.applicant import ApplicantProfile
from src.schemas.decision import DecisionDraft, RiskFactor


@runtime_checkable
class RegionAdapter(Protocol):
    """Extension point for country-specific underwriting rules.

    Only `rw.py` (Rwanda) is implemented for this demo. The protocol exists so
    a reviewer can see the one-file extension point for future markets.
    """

    country_code: str

    def extra_risk_factors(self, applicant: ApplicantProfile) -> list[RiskFactor]: ...

    def fairness_checks(self, draft: DecisionDraft, applicant: ApplicantProfile) -> list[str]: ...

    def evidence_threshold_tier(self, sum_insured_rwf: int) -> str: ...
