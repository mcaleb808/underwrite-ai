"""Unit tests for the email providers — no real HTTP calls."""

import pytest

from src.services.email.providers import (
    ConsoleProvider,
    EmailMessage,
    ResendProvider,
    get_email_provider,
)


def _msg() -> EmailMessage:
    return EmailMessage(
        to="recipient@example.com",
        subject="Hello",
        html="<p>hello</p>",
        text="hello",
    )


async def test_console_provider_sends_and_logs() -> None:
    result = await ConsoleProvider().send(_msg())
    assert result.status == "sent"
    assert result.provider_message_id == "console-noop"


async def test_resend_returns_failed_when_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.services.email.providers.settings.RESEND_API_KEY", "")
    result = await ResendProvider().send(_msg())
    assert result.status == "failed"
    assert "RESEND_API_KEY" in (result.error or "")


async def test_resend_calls_sdk_and_extracts_message_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.services.email.providers.settings.RESEND_API_KEY", "re_test")

    sent: list[dict] = []

    def _fake_send(params: dict) -> dict:
        sent.append(params)
        return {"id": "msg_fake_1"}

    import resend

    monkeypatch.setattr(resend.Emails, "send", staticmethod(_fake_send))

    result = await ResendProvider().send(_msg())

    assert result.status == "sent"
    assert result.provider_message_id == "msg_fake_1"
    assert len(sent) == 1
    assert sent[0]["to"] == ["recipient@example.com"]
    assert sent[0]["subject"] == "Hello"


async def test_resend_wraps_sdk_exceptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.services.email.providers.settings.RESEND_API_KEY", "re_test")

    def _boom(_params: dict) -> dict:
        raise RuntimeError("network down")

    import resend

    monkeypatch.setattr(resend.Emails, "send", staticmethod(_boom))

    result = await ResendProvider().send(_msg())

    assert result.status == "failed"
    assert "network down" in (result.error or "")


def test_factory_picks_provider_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.services.email.providers.settings.EMAIL_PROVIDER", "resend")
    assert isinstance(get_email_provider(), ResendProvider)

    monkeypatch.setattr("src.services.email.providers.settings.EMAIL_PROVIDER", "console")
    assert isinstance(get_email_provider(), ConsoleProvider)
