"""Email provider abstraction. Pick via settings.EMAIL_PROVIDER (resend or console)."""

from src.services.email.providers import (
    EmailMessage,
    EmailProvider,
    SendResult,
    get_email_provider,
)

__all__ = ["EmailMessage", "EmailProvider", "SendResult", "get_email_provider"]
