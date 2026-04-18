"""Email provider abstraction.

Three providers, picked by `settings.EMAIL_PROVIDER`:
- console: log the rendered email to stdout (dev default)
- resend:  POST via Resend API
- smtp:    aiosmtplib (Gmail, etc.)

The factory returns a single `EmailProvider` shaped by Protocol so callers can
swap providers without conditionals.
"""

from src.services.email.providers import (
    EmailMessage,
    EmailProvider,
    SendResult,
    get_email_provider,
)

__all__ = ["EmailMessage", "EmailProvider", "SendResult", "get_email_provider"]
