"""Email providers and the dependency factory."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from email.utils import parseaddr
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


class SendGridProvider:
    name = "sendgrid"

    async def send(self, msg: EmailMessage) -> SendResult:
        if not settings.SENDGRID_API_KEY:
            return SendResult(status="failed", error="SENDGRID_API_KEY not set")

        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Email, Mail, ReplyTo

        name, addr = parseaddr(settings.EMAIL_FROM)
        mail = Mail(
            from_email=Email(addr, name=name) if name else Email(addr),
            to_emails=msg.to,
            subject=msg.subject,
            html_content=msg.html,
            plain_text_content=msg.text,
        )
        if settings.EMAIL_REPLY_TO:
            mail.reply_to = ReplyTo(settings.EMAIL_REPLY_TO)

        client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        try:
            response = await asyncio.to_thread(client.send, mail)
        except Exception as exc:
            return SendResult(status="failed", error=repr(exc))

        message_id = None
        if response.headers is not None:
            value = response.headers.get("X-Message-Id")
            message_id = str(value) if value is not None else None
        return SendResult(status="sent", provider_message_id=message_id)


def get_email_provider() -> EmailProvider:
    """Return the provider configured in settings."""
    match settings.EMAIL_PROVIDER:
        case "sendgrid":
            return SendGridProvider()
        case _:
            return ConsoleProvider()
