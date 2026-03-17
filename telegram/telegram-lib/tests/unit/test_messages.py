"""
Unit tests for src/messages.py — read, send, edit, delete (F1–F4).
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models import ErrorCode

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
# F1 — read_messages
# -----------------------------------------------------------------------


class TestReadMessages:
    """F1: full and incremental backup via message reading."""

    @pytest.mark.asyncio
    async def test_read_messages_happy(self):
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
    async def test_read_messages_incremntal(self):
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
    async def test_read_messages_not_found(self):
        from src.messages import read_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        result = await read_messages(client, 999)

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND

    @pytest.mark.asyncio
    async def test_read_messages_no_conn(self):
        from src.messages import read_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ConnectionError("no network"))

        result = await read_messages(client, 123)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_read_messages_timeout(self):
        from src.messages import read_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=TimeoutError("timed out"))

        result = await read_messages(client, 123)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR


# -----------------------------------------------------------------------
# F2 — send_message
# -----------------------------------------------------------------------


class TestSendMessage:
    """F2: send a message under the user's account."""

    @pytest.mark.asyncio
    async def test_send_message_happy(self):
        from src.messages import send_message

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.send_message = AsyncMock(return_value=_make_tg_msg(text="Sent"))

        result = await send_message(client, 123, "Sent")

        assert result.ok
        assert result.payload.text == "Sent"
        client.send_message.assert_called_once_with(entity, "Sent")

    @pytest.mark.asyncio
    async def test_send_message_not_found(self):
        from src.messages import send_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ValueError("entity not found"))

        result = await send_message(client, 999, "Hi")

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND

    @pytest.mark.asyncio
    async def test_send_message_no_conn(self):
        from src.messages import send_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ConnectionError("no network"))

        result = await send_message(client, 123, "Hi")

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_send_message_perm_deny(self):
        from src.messages import send_message
        from telethon.errors import ChatWriteForbiddenError

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.send_message = AsyncMock(
            side_effect=ChatWriteForbiddenError(request=None)
        )

        result = await send_message(client, 123, "Hi")

        assert not result.ok
        assert result.error.code == ErrorCode.PERMISSION_DENIED


# -----------------------------------------------------------------------
# F3 — edit_message
# -----------------------------------------------------------------------


class TestEditMessage:
    """F3: edit a previously sent message."""

    @pytest.mark.asyncio
    async def test_edit_message_happy(self):
        from src.messages import edit_message

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.edit_message = AsyncMock(return_value=_make_tg_msg(text="Edited"))

        result = await edit_message(client, 123, 1, "Edited")

        assert result.ok
        assert result.payload.text == "Edited"
        client.edit_message.assert_called_once_with(entity, 1, "Edited")

    @pytest.mark.asyncio
    async def test_edit_message_not_found(self):
        from src.messages import edit_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        result = await edit_message(client, 999, 1, "New")

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND

    @pytest.mark.asyncio
    async def test_edit_message_no_change(self):
        from src.messages import edit_message
        from telethon.errors import MessageNotModifiedError

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.edit_message = AsyncMock(
            side_effect=MessageNotModifiedError(request=None)
        )

        result = await edit_message(client, 123, 1, "Same text")

        assert not result.ok
        assert result.error.code == ErrorCode.NOT_MODIFIED

    @pytest.mark.asyncio
    async def test_edit_message_no_conn(self):
        from src.messages import edit_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ConnectionError("no network"))

        result = await edit_message(client, 123, 1, "New")

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR


# -----------------------------------------------------------------------
# F4 — delete_message
# -----------------------------------------------------------------------


class TestDeleteMessage:
    """F4: delete own messages."""

    @pytest.mark.asyncio
    async def test_delete_message_happy(self):
        from src.messages import delete_message

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.delete_messages = AsyncMock()

        result = await delete_message(client, 123, [1, 2])

        assert result.ok
        assert result.payload == [1, 2]
        client.delete_messages.assert_called_once_with(entity, [1, 2])

    @pytest.mark.asyncio
    async def test_delete_message_not_found(self):
        from src.messages import delete_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        result = await delete_message(client, 999, [1])

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_message_no_conn(self):
        from src.messages import delete_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ConnectionError("no network"))

        result = await delete_message(client, 123, [1])

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_delete_message_perm_deny(self):
        from src.messages import delete_message
        from telethon.errors import MessageDeleteForbiddenError

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.delete_messages = AsyncMock(
            side_effect=MessageDeleteForbiddenError(request=None)
        )

        result = await delete_message(client, 123, [1])

        assert not result.ok
        assert result.error.code == ErrorCode.PERMISSION_DENIED
