"""Adversarial review of the decision draft for accuracy and fairness."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.adapters.rw import rw_adapter
from src.config import settings
from src.graph.state import UnderwritingState
from src.schemas.decision import Critique
from src.services.log import bind_node, get_logger, llm_observability

log = get_logger(__name__)

SYSTEM = (
    "You are an adversarial underwriting reviewer. Audit the DecisionDraft against the"
    " UW manual and the listed risk factors. Report concrete issues only — do not"
    " restate the draft. Set needs_revision=true if any of the following hold:"
    " (1) verdict does not match score per UW-130 and no hard-rule override is cited;"
    " (2) reasoning cites Ubudehe, CBHI, or district as adverse factors (UW-090,"
    " UW-140a); (3) cited rule_ids do not appear in the retrieved guidelines;"
    " (4) loading exceeds caps in cited rules; (5) any condition lacks supporting"
    " evidence in declared_history or parsed_medical (UW-140b)."
    " Set bias_flag=true if Ubudehe/CBHI/district appear as adverse factors."
)


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.STRONG_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=0,
        timeout=60,
        callbacks=[llm_observability],
    )


def _format_draft(state: UnderwritingState) -> str:
    draft = state["decision"]
    assert draft is not None
    factors = state.get("risk_factors") or []
    chunks = state.get("retrieved_guidelines") or []
    return (
        f"## Draft\nverdict={draft.verdict}\n"
        f"premium_loading_pct={draft.premium_loading_pct}\n"
        f"conditions={draft.conditions}\n"
        f"citations={draft.citations}\n"
        f"reasoning:\n{draft.reasoning}\n\n"
        f"## Risk score\n{state.get('risk_score', 0.0):.1f}"
        f" ({state.get('risk_band', 'low')})\n\n"
        f"## Risk factors\n"
        + "\n".join(f"- {f.name}: {f.evidence or ''}" for f in factors)
        + "\n\n## Retrieved rule_ids\n"
        + ", ".join(c.rule_id for c in chunks)
    )


def run(state: UnderwritingState) -> dict[str, Any]:
    bind_node(state, "critic")
    draft = state.get("decision")
    if draft is None:
        log.info("node_end", status="skipped", reason="no draft")
        return {
            "needs_revision": False,
            "revision_count": state.get("revision_count", 0) + 1,
            "events": [{"node": "critic", "type": "skipped", "reason": "no draft"}],
        }

    structured = (
        _llm()
        .with_structured_output(Critique)
        .with_retry(stop_after_attempt=2, wait_exponential_jitter=True)
    )
    try:
        llm_critique = structured.invoke(
            [SystemMessage(content=SYSTEM), HumanMessage(content=_format_draft(state))]
        )
    except Exception as exc:
        log.error("node_end", status="failed", error=repr(exc))
        return {
            "needs_revision": False,
            "revision_count": state.get("revision_count", 0) + 1,
            "events": [{"node": "critic", "type": "error", "error": repr(exc)}],
        }

    regex_issues = rw_adapter.fairness_checks(draft, state["applicant"])
    issues = list(llm_critique.issues) + regex_issues
    bias_flag = llm_critique.bias_flag or bool(regex_issues)
    needs_revision = llm_critique.needs_revision or bool(regex_issues)

    merged = Critique(
        issues=issues,
        suggestions=list(llm_critique.suggestions),
        needs_revision=needs_revision,
        bias_flag=bias_flag,
    )

    log.info(
        "node_end",
        status="done",
        issue_count=len(issues),
        regex_issue_count=len(regex_issues),
        bias_flag=bias_flag,
        needs_revision=needs_revision,
    )

    return {
        "critique": merged,
        "needs_revision": needs_revision,
        "revision_count": state.get("revision_count", 0) + 1,
        "events": [
            {
                "node": "critic",
                "type": "reviewed",
                "issue_count": len(issues),
                "bias_flag": bias_flag,
                "needs_revision": needs_revision,
                "regex_issue_count": len(regex_issues),
            }
        ],
    }
