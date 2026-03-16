"""
Unit tests for telegram-lib stateless wrapper functions.

Tests are organised by functional requirement (T10):
  F1 — read_messages (full / incremental backup)
  F2 — send_message
  F3 — edit_message
  F4 — delete_message
  F5 — get_dialogs
  F6 — download_media
  F7 — check_availability
  F8 — validate_session

All tests use mocked Telethon objects — no credentials or network needed.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import ErrorCode

# Shared fixtures -------------------------------------------------------

SINCE = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
MSG_TIME = datetime(2026, 3, 1, 12, 0, 1, tzinfo=UTC)


def _make_tg_msg(msg_id=1, text="Hello", date=MSG_TIME, media=None):
    msg = MagicMock()
    msg.id = msg_id
    msg.message = text
    msg.date = date
    msg.media = media
    msg.sender = MagicMock()
    msg.sender_id = 42
    msg.sender.first_name = "Test"
    msg.sender.title = None
    return msg


def _mock_entity(entity_id=123):
    e = MagicMock()
    e.id = entity_id
    e.username = "testuser"
    e.title = None
    e.first_name = "Test"
    return e


def _mock_client():
    client = AsyncMock()
    client.is_connected.return_value = True
    return client


# -----------------------------------------------------------------------
# F5 — get_dialogs
# -----------------------------------------------------------------------


class TestGetDialogs:
    """F5: retrieve the user's dialog list."""

    @pytest.mark.asyncio
    async def test_returns_dialog_list(self):
        from src.dialogs import get_dialogs

        dialog = MagicMock()
        dialog.id = -100123
        dialog.name = "Family Group"
        dialog.unread_count = 2
        dialog.entity = MagicMock()
        dialog.entity.__class__.__name__ = "Channel"
        type(dialog.entity).__name__ = "Channel"
        dialog.entity.username = "familygroup"

        client = _mock_client()

        async def _iter_dialogs(limit=100):
            yield dialog

        client.iter_dialogs = _iter_dialogs

        result = await get_dialogs(client, limit=10)

        assert result.ok
        assert len(result.payload) == 1
        assert result.payload[0].id == -100123
        assert result.payload[0].name == "Family Group"
        assert result.payload[0].unread_count == 2

    @pytest.mark.asyncio
    async def test_returns_error_on_connection_failure(self):
        from src.dialogs import get_dialogs

        client = _mock_client()

        async def _iter_dialogs(limit=100):
            raise ConnectionError("no network")
            yield  # make it an async generator  # noqa: E501

        client.iter_dialogs = _iter_dialogs

        result = await get_dialogs(client)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR


# -----------------------------------------------------------------------
# F1 — read_messages
# -----------------------------------------------------------------------


class TestReadMessages:
    """F1: full and incremental backup via message reading."""

    @pytest.mark.asyncio
    async def test_read_returns_messages(self):
        from src.messages import read_messages

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.get_messages = AsyncMock(return_value=[_make_tg_msg()])

        result = await read_messages(client, 123)

        assert result.ok
        assert len(result.payload) == 1
        assert result.payload[0].text == "Hello"
        assert result.payload[0].dialog_id == 123

    @pytest.mark.asyncio
    async def test_incremental_read_skips_old(self):
        from src.messages import read_messages

        old_msg = _make_tg_msg(date=SINCE)
        new_msg = _make_tg_msg(msg_id=2, text="New", date=MSG_TIME)

        client = _mock_client()
        client.get_entity = AsyncMock(return_value=_mock_entity())
        client.get_messages = AsyncMock(return_value=[old_msg, new_msg])

        result = await read_messages(client, 123, since=SINCE)

        assert result.ok
        assert len(result.payload) == 1
        assert result.payload[0].text == "New"

    @pytest.mark.asyncio
    async def test_read_entity_not_found(self):
        from src.messages import read_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        result = await read_messages(client, 999)

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND


# -----------------------------------------------------------------------
# F2 — send_message
# -----------------------------------------------------------------------


class TestSendMessage:
    """F2: send a message under the user's account."""

    @pytest.mark.asyncio
    async def test_send_returns_message_info(self):
        from src.messages import send_message

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.send_message = AsyncMock(return_value=_make_tg_msg(text="Sent"))

        result = await send_message(client, 123, "Sent")

        assert result.ok
        assert result.payload.text == "Sent"
        client.send_message.assert_called_once_with(entity, "Sent")


# -----------------------------------------------------------------------
# F3 — edit_message
# -----------------------------------------------------------------------


class TestEditMessage:
    """F3: edit a previously sent message."""

    @pytest.mark.asyncio
    async def test_edit_returns_updated_info(self):
        from src.messages import edit_message

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.edit_message = AsyncMock(return_value=_make_tg_msg(text="Edited"))

        result = await edit_message(client, 123, 1, "Edited")

        assert result.ok
        assert result.payload.text == "Edited"
        client.edit_message.assert_called_once_with(entity, 1, "Edited")


# -----------------------------------------------------------------------
# F4 — delete_message
# -----------------------------------------------------------------------


class TestDeleteMessage:
    """F4: delete own messages."""

    @pytest.mark.asyncio
    async def test_delete_returns_deleted_ids(self):
        from src.messages import delete_message

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.delete_messages = AsyncMock()

        result = await delete_message(client, 123, [1, 2])

        assert result.ok
        assert result.payload == [1, 2]
        client.delete_messages.assert_called_once_with(entity, [1, 2])


# -----------------------------------------------------------------------
# F6 — download_media
# -----------------------------------------------------------------------


class TestDownloadMedia:
    """F6: download photos and media files."""

    @pytest.mark.asyncio
    async def test_download_no_media(self):
        from src.media import download_media

        msg = _make_tg_msg(media=None)
        client = _mock_client()
        client.get_entity = AsyncMock(return_value=_mock_entity())
        client.get_messages = AsyncMock(return_value=[msg])

        result = await download_media(client, 123, 1)

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND
        assert "no media" in result.error.message

    @pytest.mark.asyncio
    async def test_download_message_not_found(self):
        from src.media import download_media

        client = _mock_client()
        client.get_entity = AsyncMock(return_value=_mock_entity())
        client.get_messages = AsyncMock(return_value=[None])

        result = await download_media(client, 123, 999)

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND


# -----------------------------------------------------------------------
# F7 — check_availability
# -----------------------------------------------------------------------


class TestCheckAvailability:
    """F7: verify Telegram is reachable."""

    @pytest.mark.asyncio
    async def test_available(self):
        from src.health import check_availability

        client = _mock_client()
        client.is_connected = MagicMock(return_value=True)
        client.get_me = AsyncMock(return_value=MagicMock())

        result = await check_availability(client)

        assert result.ok
        assert result.payload.available is True
        assert result.payload.latency_ms is not None


# -----------------------------------------------------------------------
# F8 — validate_session
# -----------------------------------------------------------------------


class TestValidateSession:
    """F8: validate the current user session."""

    @pytest.mark.asyncio
    async def test_valid_session(self):
        from src.health import validate_session

        me = MagicMock()
        me.id = 42
        me.first_name = "Test"
        me.last_name = "User"
        me.username = "testuser"
        me.phone = "+1234567890"

        client = _mock_client()
        client.get_me = AsyncMock(return_value=me)

        result = await validate_session(client)

        assert result.ok
        assert result.payload.valid is True
        assert result.payload.user_id == 42
        assert result.payload.username == "testuser"

    @pytest.mark.asyncio
    async def test_invalid_session(self):
        from src.health import validate_session

        client = _mock_client()
        client.get_me = AsyncMock(return_value=None)

        result = await validate_session(client)

        assert not result.ok
        assert result.error.code == ErrorCode.SESSION_INVALID


# -----------------------------------------------------------------------
# Error handling (T3) — rate limiting
# -----------------------------------------------------------------------


class TestErrorHandling:
    """T3: library catches all exceptions and returns TgError."""

    @pytest.mark.asyncio
    async def test_rate_limit_returns_retry_after(self):
        from telethon.errors import FloodWaitError

        from src.messages import read_messages

        client = _mock_client()
        exc = FloodWaitError(request=None, capture=30)
        client.get_entity = AsyncMock(side_effect=exc)

        result = await read_messages(client, 123)

        assert not result.ok
        assert result.error.code == ErrorCode.RATE_LIMITED
        assert result.error.retry_after == 30.0


# -----------------------------------------------------------------------
# Timeout handling — asyncio.TimeoutError → NETWORK_ERROR
# -----------------------------------------------------------------------


class TestTimeoutHandling:
    """Timeout errors must be reported as NETWORK_ERROR."""

    @pytest.mark.asyncio
    async def test_ping_timeout(self):
        import asyncio

        from src.health import check_availability

        client = _mock_client()
        client.get_me = AsyncMock(side_effect=asyncio.TimeoutError())

        result = await check_availability(client)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_get_dialogs_timeout(self):
        import asyncio

        from src.dialogs import get_dialogs

        client = _mock_client()

        async def _iter_timeout(limit=100):
            raise asyncio.TimeoutError()
            yield  # noqa: E501

        client.iter_dialogs = _iter_timeout

        result = await get_dialogs(client)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_read_messages_timeout(self):
        import asyncio

        from src.messages import read_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=asyncio.TimeoutError())

        result = await read_messages(client, 123)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_send_message_timeout(self):
        import asyncio

        from src.messages import send_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=asyncio.TimeoutError())

        result = await send_message(client, 123, "Hello")

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

