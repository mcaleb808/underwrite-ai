"""Email providers and the dependency factory."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from src.config import settings

log = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    to: str
    subject: str
    html: str
    text: str | None = None


@dataclass
class SendResult:
    status: str  # "sent" | "failed"
    provider_message_id: str | None = None
    error: str | None = None


class EmailProvider(Protocol):
    name: str

    async def send(self, msg: EmailMessage) -> SendResult: ...


class ConsoleProvider:
    name = "console"

    async def send(self, msg: EmailMessage) -> SendResult:
        log.info("email[console] -> %s | %s\n%s", msg.to, msg.subject, msg.text or msg.html)
        return SendResult(status="sent", provider_message_id="console-noop")


class ResendProvider:
    name = "resend"

    async def send(self, msg: EmailMessage) -> SendResult:
        if not settings.RESEND_API_KEY:
            return SendResult(status="failed", error="RESEND_API_KEY not set")
        import resend

        resend.api_key = settings.RESEND_API_KEY
        try:
            params: dict = {
                "from": settings.EMAIL_FROM,
                "to": [msg.to],
                "subject": msg.subject,
                "html": msg.html,
                "reply_to": settings.EMAIL_REPLY_TO,
            }
            if msg.text:
                params["text"] = msg.text
            response = resend.Emails.send(params)
            return SendResult(status="sent", provider_message_id=str(response.get("id")))
        except Exception as exc:
            return SendResult(status="failed", error=repr(exc))


class SmtpProvider:
    name = "smtp"

    async def send(self, msg: EmailMessage) -> SendResult:
        from email.message import EmailMessage as MIMEMessage

        import aiosmtplib

        mime = MIMEMessage()
        mime["From"] = settings.EMAIL_FROM
        mime["To"] = msg.to
        mime["Subject"] = msg.subject
        mime["Reply-To"] = settings.EMAIL_REPLY_TO
        mime.set_content(msg.text or "")
        mime.add_alternative(msg.html, subtype="html")
        try:
            await aiosmtplib.send(
                mime,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASS,
                start_tls=True,
            )
            return SendResult(status="sent", provider_message_id=mime["Message-Id"])
        except Exception as exc:
            return SendResult(status="failed", error=repr(exc))


def get_email_provider() -> EmailProvider:
    """FastAPI dependency: return the provider configured in settings."""
    match settings.EMAIL_PROVIDER:
        case "resend":
            return ResendProvider()
        case "smtp":
            return SmtpProvider()
        case _:
            return ConsoleProvider()
