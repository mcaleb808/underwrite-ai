"""Unit tests for the email providers — no real SMTP / HTTP calls."""

from types import SimpleNamespace

import pytest

from src.services.email.providers import (
    ConsoleProvider,
    EmailMessage,
    SendGridProvider,
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


async def test_sendgrid_returns_failed_when_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.services.email.providers.settings.SENDGRID_API_KEY", "")
    result = await SendGridProvider().send(_msg())
    assert result.status == "failed"
    assert "SENDGRID_API_KEY" in (result.error or "")


async def test_sendgrid_calls_client_and_extracts_message_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.services.email.providers.settings.SENDGRID_API_KEY", "SG.test")

    sent: list[object] = []
    fake_response = SimpleNamespace(
        status_code=202,
        body=b"",
        headers={"X-Message-Id": "fake-msg-1"},
    )

    class _FakeClient:
        def __init__(self, _key: str) -> None:
            pass

        def send(self, mail: object):
            sent.append(mail)
            return fake_response

    monkeypatch.setattr("sendgrid.SendGridAPIClient", _FakeClient)

    result = await SendGridProvider().send(_msg())

    assert result.status == "sent"
    assert result.provider_message_id == "fake-msg-1"
    assert len(sent) == 1


async def test_sendgrid_wraps_client_exceptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.services.email.providers.settings.SENDGRID_API_KEY", "SG.test")

    class _BoomClient:
        def __init__(self, _key: str) -> None:
            pass

        def send(self, _mail: object):
            raise RuntimeError("network down")

    monkeypatch.setattr("sendgrid.SendGridAPIClient", _BoomClient)

    result = await SendGridProvider().send(_msg())

    assert result.status == "failed"
    assert "network down" in (result.error or "")


def test_factory_picks_provider_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.services.email.providers.settings.EMAIL_PROVIDER", "sendgrid")
    assert isinstance(get_email_provider(), SendGridProvider)

    monkeypatch.setattr("src.services.email.providers.settings.EMAIL_PROVIDER", "console")
    assert isinstance(get_email_provider(), ConsoleProvider)
