"""Unit tests for Telegram Reader and Writer."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.interfaces import Message, MessengerAccount

CREDS = json.dumps({"api_id": 12345, "api_hash": "test_hash", "session": ""})
ACCOUNT = MessengerAccount(
    messenger_id="telegram",
    account_id="test_peer",
    credentials_ref="TG_CREDS",
)
SINCE = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
MSG_TIME = datetime(2026, 3, 1, 12, 0, 1, tzinfo=UTC)


def _make_tg_msg(msg_id=1, text="Hello", date=MSG_TIME):
    msg = MagicMock()
    msg.id = msg_id
    msg.message = text
    msg.date = date
    msg.media = None
    return msg


def _make_mock_client(messages=None):
    """Build a mock TelegramClient async context manager."""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    async def _iter(*args, **kwargs):
        for m in messages or []:
            yield m

    client.iter_messages = _iter
    client.send_message = AsyncMock()
    client.forward_messages = AsyncMock()
    return client


# ---------------------------------------------------------------------------
# Reader tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_telegram_reader_returns_messages_after_since():
    from src.messengers.telegram.reader import TelegramReader

    mock_client = _make_mock_client([_make_tg_msg()])
    with (
        patch("src.messengers.telegram.reader.TelegramClient", return_value=mock_client),
        patch.dict(os.environ, {"TG_CREDS": CREDS}),
    ):
        messages = await TelegramReader().read_since(ACCOUNT, SINCE)

    assert len(messages) == 1
    assert messages[0].text == "Hello"
    assert messages[0].source_messenger == "telegram"
    assert messages[0].metadata["peer_id"] == "test_peer"


@pytest.mark.asyncio
async def test_telegram_reader_skips_messages_at_or_before_since():
    from src.messengers.telegram.reader import TelegramReader

    old_msg = _make_tg_msg(date=SINCE)  # exactly at since — must be excluded
    mock_client = _make_mock_client([old_msg])
    with (
        patch("src.messengers.telegram.reader.TelegramClient", return_value=mock_client),
        patch.dict(os.environ, {"TG_CREDS": CREDS}),
    ):
        messages = await TelegramReader().read_since(ACCOUNT, SINCE)

    assert messages == []


@pytest.mark.asyncio
async def test_telegram_reader_raises_on_missing_credentials():
    from src.messengers.telegram.reader import TelegramReader

    clean_env = {k: v for k, v in os.environ.items() if k != "TG_CREDS"}
    with (
        patch.dict(os.environ, clean_env, clear=True),
        pytest.raises(OSError, match="TG_CREDS"),
    ):
        await TelegramReader().read_since(ACCOUNT, SINCE)


# ---------------------------------------------------------------------------
# Writer tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_telegram_writer_reposts_cross_messenger_message():
    from src.messengers.telegram.writer import TelegramWriter

    msg = Message(id="1", text="Hi from VK", timestamp=MSG_TIME, source_messenger="vk")
    mock_client = _make_mock_client()
    with (
        patch("src.messengers.telegram.writer.TelegramClient", return_value=mock_client),
        patch.dict(os.environ, {"TG_CREDS": CREDS}),
    ):
        await TelegramWriter(strategy="repost").write(ACCOUNT, [msg])

    mock_client.send_message.assert_called_once()
    call_text = mock_client.send_message.call_args[0][1]
    assert "[From Vk]" in call_text
    assert "Hi from VK" in call_text


@pytest.mark.asyncio
async def test_telegram_writer_forwards_telegram_message():
    from src.messengers.telegram.writer import TelegramWriter

    msg = Message(
        id="42",
        text="Hello",
        timestamp=MSG_TIME,
        source_messenger="telegram",
        metadata={"peer_id": "source_peer", "message_id": 42},
    )
    mock_client = _make_mock_client()
    with (
        patch("src.messengers.telegram.writer.TelegramClient", return_value=mock_client),
        patch.dict(os.environ, {"TG_CREDS": CREDS}),
    ):
        await TelegramWriter(strategy="forward").write(ACCOUNT, [msg])

    mock_client.forward_messages.assert_called_once_with(
        "test_peer", [42], from_peer="source_peer"
    )
    mock_client.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_telegram_writer_reposts_when_forward_strategy_but_source_is_vk():
    from src.messengers.telegram.writer import TelegramWriter

    msg = Message(
        id="1",
        text="Cross-platform",
        timestamp=MSG_TIME,
        source_messenger="vk",
        metadata={"peer_id": "12345", "message_id": 1},
    )
    mock_client = _make_mock_client()
    with (
        patch("src.messengers.telegram.writer.TelegramClient", return_value=mock_client),
        patch.dict(os.environ, {"TG_CREDS": CREDS}),
    ):
        await TelegramWriter(strategy="forward").write(ACCOUNT, [msg])

    mock_client.send_message.assert_called_once()
    mock_client.forward_messages.assert_not_called()


@pytest.mark.asyncio
async def test_telegram_writer_adds_no_attribution_for_same_messenger():
    from src.messengers.telegram.writer import TelegramWriter

    msg = Message(id="1", text="Own message", timestamp=MSG_TIME, source_messenger="telegram")
    mock_client = _make_mock_client()
    with (
        patch("src.messengers.telegram.writer.TelegramClient", return_value=mock_client),
        patch.dict(os.environ, {"TG_CREDS": CREDS}),
    ):
        await TelegramWriter(strategy="repost").write(ACCOUNT, [msg])

    call_text = mock_client.send_message.call_args[0][1]
    assert "[From" not in call_text
    assert call_text == "Own message"
