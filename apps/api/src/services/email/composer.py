"""Compose customer-facing emails from a decision via LLM, with a safe fallback."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.config import settings
from src.schemas.decision import DecisionDraft
from src.services.log import get_logger, llm_observability

log = get_logger(__name__)

SYSTEM = """\
You write the body of a customer-facing email from an insurance company to an
applicant about an underwriting decision. Your output is what the customer reads,
not internal documentation.

Tone:
- Warm, professional, empathetic, plain English
- 2-4 short paragraphs
- Address the applicant by their first name in the opening line
- Sign off with the insurer's name on the last line

Hard prohibitions (the customer must NEVER see these):
- Internal rule IDs of any kind (UW-010, UW-130, etc.)
- The words "verdict", "score", "band", "loading", "draft", "critic", "evaluation"
- The raw verdict string ("accept", "accept_with_conditions", "refer", "decline")
  - translate to natural English
- Any numeric premium percentage
- The technical reasoning paragraph

Verdict-specific tone:
- accept: warmly congratulate; one sentence on what happens next (welcome pack
  or coverage activation soon)
- accept_with_conditions: positive overall; explain each condition in customer
  language (rewrite anything technical); if a premium adjustment applies,
  mention it qualitatively in one sentence (e.g. "your monthly premium reflects
  a moderate adjustment based on factors in your application") with no specific
  percentage
- refer: reassure that a senior member of the underwriting team will follow up
  within a few business days; invite questions
- decline: empathetic; explain that the policy as applied for cannot be issued
  at this time; invite the applicant to reach out with questions or to discuss
  alternatives

Always include the reference number once, and invite a reply to the reply-to
address for any questions.

Return strict JSON: {"subject": "...", "body": "..."}. The subject should be
short (under 80 chars), include the insurer name and the reference number, and
not contain the raw verdict enum.
"""


class ComposedEmail(BaseModel):
    subject: str = Field(min_length=5, max_length=120)
    body: str = Field(min_length=40)


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.FAST_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=0.4,
        timeout=30,
        callbacks=[llm_observability],
    )


_FALLBACK_HEADLINES: dict[str, str] = {
    "accept": "Your application has been approved",
    "accept_with_conditions": "Your application has been approved with some conditions",
    "refer": "Your application is under further review",
    "decline": "Update on your application",
}


def _fallback(reference: str, first_name: str, verdict: str) -> ComposedEmail:
    headline = _FALLBACK_HEADLINES.get(verdict, "Update on your application")
    body = (
        f"Dear {first_name},\n\n"
        f"{headline}. Your reference number is {reference}.\n\n"
        f"A member of our team will be in touch shortly with the full details.\n\n"
        f"If you have any questions in the meantime, please reply to this email or write to "
        f"{settings.EMAIL_REPLY_TO}.\n\n"
        f"-- {settings.INSURER_NAME}"
    )
    subject = f"{settings.INSURER_NAME} - {headline} ({reference})"
    return ComposedEmail(subject=subject, body=body)


def compose(reference: str, first_name: str, decision: DecisionDraft) -> ComposedEmail:
    """Compose a customer subject + body via LLM; fall back to a template on failure."""
    has_premium_adjustment = decision.premium_loading_pct > 0
    conditions_block = (
        "\n".join(f"- {c}" for c in decision.conditions) if decision.conditions else "(none)"
    )

    user_input = (
        f"Applicant first name: {first_name}\n"
        f"Reference number: {reference}\n"
        f"Insurer name: {settings.INSURER_NAME}\n"
        f"Reply-to address: {settings.EMAIL_REPLY_TO}\n"
        f"\n"
        f"Decision verdict (for tone selection only - do not echo): {decision.verdict}\n"
        f"Premium adjustment applies: {'yes' if has_premium_adjustment else 'no'}\n"
        f"\n"
        f"Conditions to communicate (rewrite each into plain customer language; "
        f"strip any 'per UW-XXX' references):\n"
        f"{conditions_block}\n"
    )

    structured = (
        _llm()
        .with_structured_output(ComposedEmail)
        .with_retry(stop_after_attempt=2, wait_exponential_jitter=True)
    )
    try:
        return structured.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=user_input)])
    except Exception as exc:
        log.error("email_compose_failed", error=repr(exc), verdict=decision.verdict)
        return _fallback(reference, first_name, decision.verdict)
