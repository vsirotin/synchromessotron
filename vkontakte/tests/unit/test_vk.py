"""Unit tests for VK Reader and Writer.

Reader and writer sync methods are tested directly (_read_sync / _write_sync)
to avoid asyncio.to_thread complexity in unit tests.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.core.interfaces import Message, MessengerAccount

CREDS = json.dumps({"token": "test_vk_token"})
ACCOUNT = MessengerAccount(
    messenger_id="vk",
    account_id="123456",
    credentials_ref="VK_CREDS",
)
SINCE = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
SINCE_TS = int(SINCE.timestamp())


def _vk_msg(msg_id=1, text="Hello", date_offset=1, peer_id=123456):
    return {"id": msg_id, "text": text, "date": SINCE_TS + date_offset, "peer_id": peer_id}


def _make_vk_api(items=None):
    vk = MagicMock()
    vk.messages.getHistory.return_value = {"items": items or []}
    return vk


def _make_session(vk_api_obj):
    session = MagicMock()
    session.get_api.return_value = vk_api_obj
    return session


# ---------------------------------------------------------------------------
# Reader tests
# ---------------------------------------------------------------------------


def test_vk_reader_returns_messages_after_since():
    from src.messengers.vk.reader import VKReader

    fake_vk = _make_vk_api([_vk_msg()])
    with (
        patch("src.messengers.vk.reader.vk_api.VkApi", return_value=_make_session(fake_vk)),
        patch.dict(os.environ, {"VK_CREDS": CREDS}),
    ):
        messages = VKReader()._read_sync(ACCOUNT, SINCE)

    assert len(messages) == 1
    assert messages[0].text == "Hello"
    assert messages[0].source_messenger == "vk"
    assert messages[0].metadata["peer_id"] == 123456


def test_vk_reader_excludes_messages_at_or_before_since():
    from src.messengers.vk.reader import VKReader

    old_msg = {"id": 99, "text": "Old", "date": SINCE_TS - 1, "peer_id": 123456}
    fake_vk = _make_vk_api([_vk_msg(date_offset=1), old_msg])
    with (
        patch("src.messengers.vk.reader.vk_api.VkApi", return_value=_make_session(fake_vk)),
        patch.dict(os.environ, {"VK_CREDS": CREDS}),
    ):
        messages = VKReader()._read_sync(ACCOUNT, SINCE)

    assert len(messages) == 1


def test_vk_reader_returns_messages_sorted_oldest_first():
    from src.messengers.vk.reader import VKReader

    # VK returns newest first; reader must reverse to oldest first
    items = [
        _vk_msg(msg_id=2, date_offset=2),
        _vk_msg(msg_id=1, date_offset=1),
    ]
    fake_vk = _make_vk_api(items)
    with (
        patch("src.messengers.vk.reader.vk_api.VkApi", return_value=_make_session(fake_vk)),
        patch.dict(os.environ, {"VK_CREDS": CREDS}),
    ):
        messages = VKReader()._read_sync(ACCOUNT, SINCE)

    assert [m.id for m in messages] == ["1", "2"]


def test_vk_reader_raises_on_missing_credentials():
    from src.messengers.vk.reader import _load_credentials

    clean_env = {k: v for k, v in os.environ.items() if k != "MISSING_CRED"}
    with (
        patch.dict(os.environ, clean_env, clear=True),
        pytest.raises(OSError, match="MISSING_CRED"),
    ):
        _load_credentials("MISSING_CRED")


# ---------------------------------------------------------------------------
# Writer tests
# ---------------------------------------------------------------------------


def test_vk_writer_reposts_cross_messenger_message():
    from src.messengers.vk.writer import VKWriter

    msg = Message(id="1", text="Hi from Telegram", timestamp=SINCE, source_messenger="telegram")
    fake_vk = MagicMock()
    with (
        patch("src.messengers.vk.writer.vk_api.VkApi", return_value=_make_session(fake_vk)),
        patch.dict(os.environ, {"VK_CREDS": CREDS}),
    ):
        VKWriter(strategy="repost")._write_sync(ACCOUNT, [msg])

    fake_vk.messages.send.assert_called_once()
    kwargs = fake_vk.messages.send.call_args.kwargs
    assert kwargs["peer_id"] == 123456
    assert "[From Telegram]" in kwargs["message"]
    assert "Hi from Telegram" in kwargs["message"]


def test_vk_writer_forwards_vk_message():
    from src.messengers.vk.writer import VKWriter

    msg = Message(
        id="42",
        text="Hello",
        timestamp=SINCE,
        source_messenger="vk",
        metadata={"peer_id": 789, "message_id": 42},
    )
    fake_vk = MagicMock()
    with (
        patch("src.messengers.vk.writer.vk_api.VkApi", return_value=_make_session(fake_vk)),
        patch.dict(os.environ, {"VK_CREDS": CREDS}),
    ):
        VKWriter(strategy="forward")._write_sync(ACCOUNT, [msg])

    kwargs = fake_vk.messages.send.call_args.kwargs
    assert "forward" in kwargs


def test_vk_writer_reposts_even_with_forward_strategy_for_cross_messenger():
    from src.messengers.vk.writer import VKWriter

    msg = Message(
        id="1",
        text="Cross",
        timestamp=SINCE,
        source_messenger="telegram",
        metadata={"peer_id": 789, "message_id": 1},
    )
    fake_vk = MagicMock()
    with (
        patch("src.messengers.vk.writer.vk_api.VkApi", return_value=_make_session(fake_vk)),
        patch.dict(os.environ, {"VK_CREDS": CREDS}),
    ):
        VKWriter(strategy="forward")._write_sync(ACCOUNT, [msg])

    kwargs = fake_vk.messages.send.call_args.kwargs
    assert "forward" not in kwargs
    assert "[From Telegram]" in kwargs["message"]


def test_vk_writer_random_id_is_deterministic():
    from src.messengers.vk.writer import _random_id

    rid1 = _random_id(123, "1", "hello")
    rid2 = _random_id(123, "1", "hello")
    rid3 = _random_id(123, "1", "different text")

    assert rid1 == rid2
    assert rid1 != rid3
    assert -(2**31) <= rid1 <= 2**31 - 1  # must fit in signed 32-bit int
