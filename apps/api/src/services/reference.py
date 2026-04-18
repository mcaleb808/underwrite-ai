"""Generate human-friendly reference numbers for tasks."""

import secrets
from datetime import UTC, datetime


def new_reference(now: datetime | None = None) -> str:
    """Format: UW-YYYY-NNNNNN where N is a 6-char hex token."""
    year = (now or datetime.now(UTC)).year
    token = secrets.token_hex(3).upper()
    return f"UW-{year}-{token}"
