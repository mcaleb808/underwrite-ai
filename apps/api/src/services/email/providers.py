"""Email providers and the dependency factory."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

from src.config import settings
from src.services.log import get_logger

log = get_logger(__name__)


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
        log.info(
            "email_console",
            to=msg.to,
            subject=msg.subject,
            body=(msg.text or msg.html)[:1000],
        )
        return SendResult(status="sent", provider_message_id="console-noop")


class ResendProvider:
    name = "resend"

    async def send(self, msg: EmailMessage) -> SendResult:
        if not settings.RESEND_API_KEY:
            log.warning("email_send", provider="resend", status="failed", reason="no api key")
            return SendResult(status="failed", error="RESEND_API_KEY not set")

        import resend

        resend.api_key = settings.RESEND_API_KEY
        params: dict = {
            "from": settings.EMAIL_FROM,
            "to": [msg.to],
            "subject": msg.subject,
            "html": msg.html,
            "reply_to": settings.EMAIL_REPLY_TO,
        }
        if msg.text:
            params["text"] = msg.text

        try:
            response = await asyncio.to_thread(resend.Emails.send, params)
        except Exception as exc:
            log.error("email_send", provider="resend", status="failed", error=repr(exc))
            return SendResult(status="failed", error=repr(exc))

        message_id = str(response.get("id")) if response else None
        log.info(
            "email_send",
            provider="resend",
            status="sent",
            to=msg.to,
            message_id=message_id,
        )
        return SendResult(status="sent", provider_message_id=message_id)


def get_email_provider() -> EmailProvider:
    """Return the provider configured in settings."""
    match settings.EMAIL_PROVIDER:
        case "resend":
            return ResendProvider()
        case _:
            return ConsoleProvider()
