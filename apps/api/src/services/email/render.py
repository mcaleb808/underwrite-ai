"""Render the underwriting decision into a customer-facing email."""

from __future__ import annotations

from html import escape

from src.schemas.decision import DecisionDraft
from src.services.email.composer import compose


def render(reference: str, applicant_name: str, decision: DecisionDraft) -> tuple[str, str, str]:
    """Return (subject, html, text) for the email shown to the applicant."""
    first_name = (applicant_name.split()[0] if applicant_name else "there").strip() or "there"
    composed = compose(reference, first_name, decision)
    return composed.subject, _to_html(composed.body), composed.body


def _to_html(body: str) -> str:
    paragraphs = "".join(
        f"<p>{escape(p).replace(chr(10), '<br>')}</p>" for p in body.split("\n\n") if p.strip()
    )
    return (
        '<!doctype html><html><body style="font-family:ui-sans-serif,system-ui,sans-serif;'
        'color:#111;line-height:1.55;max-width:560px;margin:0 auto;padding:24px;">'
        f"{paragraphs}"
        "</body></html>"
    )
