"""Render the underwriting decision into a plain-text + minimal HTML email."""

from __future__ import annotations

from src.config import settings
from src.schemas.decision import DecisionDraft

_VERDICT_HEADLINES: dict[str, str] = {
    "accept": "Your application has been approved",
    "accept_with_conditions": "Your application is approved with conditions",
    "refer": "Your application is under further review",
    "decline": "Update on your application",
}


def render(reference: str, applicant_name: str, decision: DecisionDraft) -> tuple[str, str, str]:
    """Return (subject, html, text)."""
    headline = _VERDICT_HEADLINES.get(decision.verdict, "Underwriting decision")
    subject = f"{settings.INSURER_NAME} — {headline} ({reference})"

    bullets_text = "\n".join(f"  - {c}" for c in decision.conditions) or "  (none)"
    bullets_html = (
        "<ul>" + "".join(f"<li>{c}</li>" for c in decision.conditions) + "</ul>"
        if decision.conditions
        else "<p><em>No conditions.</em></p>"
    )
    citations = ", ".join(decision.citations) or "—"

    text = f"""Dear {applicant_name},

{headline}.

Reference: {reference}
Verdict: {decision.verdict.replace("_", " ")}
Premium loading: +{decision.premium_loading_pct:.1f}%

Conditions:
{bullets_text}

Reasoning:
{decision.reasoning}

Cited rules: {citations}

— {settings.INSURER_NAME}
"""

    html = f"""<!doctype html>
<html><body style="font-family: ui-sans-serif, system-ui, sans-serif; color:#111;">
  <p>Dear {applicant_name},</p>
  <p><strong>{headline}.</strong></p>
  <p><strong>Reference:</strong> {reference}<br>
     <strong>Verdict:</strong> {decision.verdict.replace("_", " ")}<br>
     <strong>Premium loading:</strong> +{decision.premium_loading_pct:.1f}%</p>
  <h4 style="margin-bottom:4px">Conditions</h4>
  {bullets_html}
  <h4 style="margin-bottom:4px">Reasoning</h4>
  <p style="white-space:pre-line">{decision.reasoning}</p>
  <p style="color:#666;font-size:12px">Cited rules: {citations}</p>
  <p style="color:#666;font-size:12px">— {settings.INSURER_NAME}</p>
</body></html>"""

    return subject, html, text
