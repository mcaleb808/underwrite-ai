"""Draft an underwriting decision from risk factors + retrieved guidelines."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import settings
from src.graph.state import UnderwritingState
from src.schemas.applicant import ApplicantProfile
from src.schemas.decision import DecisionDraft, GuidelineChunk, RiskFactor
from src.services.log import bind, get_logger, llm_observability

log = get_logger(__name__)

SYSTEM = (
    "You are a senior underwriter for a Rwandan health insurer."
    " Produce a single DecisionDraft strictly grounded in the provided risk factors"
    " and retrieved guideline chunks. Cite rule_ids you actually used in `citations`."
    " Map score to verdict per UW-130 unless a hard rule (UW-040 HbA1c>8.5,"
    " UW-060 active TB, UW-050 non-adherent HIV) overrides. Never cite Ubudehe,"
    " CBHI, or district-of-residence as adverse factors (UW-090, UW-140)."
    " Premium loadings must come from cited rules; do not invent percentages."
)


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.STRONG_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=0,
        callbacks=[llm_observability],
    )


def _format_factors(factors: list[RiskFactor]) -> str:
    if not factors:
        return "(none)"
    return "\n".join(f"- {f.name} (+{f.contribution:.1f}): {f.evidence or ''}" for f in factors)


def _format_guidelines(chunks: list[GuidelineChunk]) -> str:
    if not chunks:
        return "(none retrieved)"
    return "\n\n".join(f"[{c.rule_id}] {c.section_title}\n{c.text}" for c in chunks)


def _format_applicant(p: ApplicantProfile) -> str:
    return (
        f"applicant_id={p.applicant_id}\n"
        f"sex={p.demographics.sex} dob={p.demographics.dob}\n"
        f"district={p.demographics.district} province={p.demographics.province}\n"
        f"occupation={p.occupation.title} (class {p.occupation.class_})\n"
        f"sum_insured_rwf={p.sum_insured_rwf}\n"
        f"declared_history={p.declared_history}"
    )


def run(state: UnderwritingState) -> dict[str, Any]:
    bind(node="decision_draft", task_id=state.get("task_id"))
    profile = state["applicant"]
    factors = state.get("risk_factors") or []
    chunks = state.get("retrieved_guidelines") or []
    score = state.get("risk_score", 0.0)
    band = state.get("risk_band", "low")
    critique = state.get("critique")
    is_revision = critique is not None
    log.info("node_start", risk_score=score, risk_band=band, is_revision=is_revision)

    user_parts = [
        f"## Applicant\n{_format_applicant(profile)}",
        f"\n## Risk score\n{score:.1f} ({band})",
        f"\n## Risk factors\n{_format_factors(factors)}",
        f"\n## Retrieved guidelines\n{_format_guidelines(chunks)}",
    ]
    if critique is not None and critique.issues:
        user_parts.append(
            "\n## Critic feedback (must address before finalizing)\n"
            + "\n".join(f"- {issue}" for issue in critique.issues)
        )
        if critique.suggestions:
            user_parts.append("Suggestions:\n" + "\n".join(f"- {s}" for s in critique.suggestions))

    structured = _llm().with_structured_output(DecisionDraft)
    draft = structured.invoke(
        [SystemMessage(content=SYSTEM), HumanMessage(content="\n".join(user_parts))]
    )

    log.info(
        "node_end",
        verdict=draft.verdict,
        premium_loading_pct=draft.premium_loading_pct,
        citation_count=len(draft.citations),
    )

    return {
        "decision": draft,
        "events": [
            {
                "node": "decision_draft",
                "type": "drafted",
                "verdict": draft.verdict,
                "premium_loading_pct": draft.premium_loading_pct,
                "citations": draft.citations,
                "is_revision": is_revision,
            }
        ],
    }
