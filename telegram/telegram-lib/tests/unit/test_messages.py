"""
Unit tests for src/messages.py — read, send, edit, delete (F1–F4).
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import telethon.tl.types as tl_types

from telegram_lib.models import ErrorCode

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
# _get_media_type helper
# -----------------------------------------------------------------------

class TestGetMediaType:
    """Unit tests for the _get_media_type helper."""

    def test_none_returns_none(self):
        from telegram_lib.messages import _get_media_type

        assert _get_media_type(None) is None

    def test_photo(self):
        from telegram_lib.messages import _get_media_type

        media = MagicMock(spec=tl_types.MessageMediaPhoto)
        assert _get_media_type(media) == "photo"

    def test_document_video(self):
        from telegram_lib.messages import _get_media_type

        attr_video = MagicMock(spec=tl_types.DocumentAttributeVideo)
        doc = MagicMock()
        doc.attributes = [attr_video]
        media = MagicMock(spec=tl_types.MessageMediaDocument)
        media.document = doc
        assert _get_media_type(media) == "video"

    def test_document_audio_music(self):
        from telegram_lib.messages import _get_media_type

        attr_audio = MagicMock(spec=tl_types.DocumentAttributeAudio)
        attr_audio.voice = False
        doc = MagicMock()
        doc.attributes = [attr_audio]
        media = MagicMock(spec=tl_types.MessageMediaDocument)
        media.document = doc
        assert _get_media_type(media) == "audio"

    def test_document_audio_voice(self):
        from telegram_lib.messages import _get_media_type

        attr_audio = MagicMock(spec=tl_types.DocumentAttributeAudio)
        attr_audio.voice = True
        doc = MagicMock()
        doc.attributes = [attr_audio]
        media = MagicMock(spec=tl_types.MessageMediaDocument)
        media.document = doc
        assert _get_media_type(media) == "voice"

    def test_document_animated_gif(self):
        from telegram_lib.messages import _get_media_type

        attr_animated = MagicMock(spec=tl_types.DocumentAttributeAnimated)
        doc = MagicMock()
        doc.attributes = [attr_animated]
        media = MagicMock(spec=tl_types.MessageMediaDocument)
        media.document = doc
        assert _get_media_type(media) == "gif"

    def test_document_generic(self):
        from telegram_lib.messages import _get_media_type

        attr_filename = MagicMock(spec=tl_types.DocumentAttributeFilename)
        doc = MagicMock()
        doc.attributes = [attr_filename]
        media = MagicMock(spec=tl_types.MessageMediaDocument)
        media.document = doc
        assert _get_media_type(media) == "document"

    def test_webpage(self):
        from telegram_lib.messages import _get_media_type

        media = MagicMock(spec=tl_types.MessageMediaWebPage)
        assert _get_media_type(media) == "webpage"


# -----------------------------------------------------------------------
# F1 — read_messages
# -----------------------------------------------------------------------


class TestReadMessages:
    """F1: full and incremental backup via message reading."""

    @pytest.mark.asyncio
    async def test_read_messages_happy(self):
        from telegram_lib.messages import read_messages

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
        from telegram_lib.messages import read_messages

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
        from telegram_lib.messages import read_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        result = await read_messages(client, 999)

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND

    @pytest.mark.asyncio
    async def test_read_messages_no_conn(self):
        from telegram_lib.messages import read_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ConnectionError("no network"))

        result = await read_messages(client, 123)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_read_messages_timeout(self):
        from telegram_lib.messages import read_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=TimeoutError("timed out"))

        result = await read_messages(client, 123)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_read_messages_for_pagination_uses_backward_direction(self):
        """When for_pagination=True, Telethon must be called with reverse=False.

        Regression test for the full-backup slowdown bug:
        Previously `reverse = since is not None` evaluated to True for pagination,
        causing Telethon to walk FORWARD in time (returning the same newest messages
        on every page).  The fix changes the expression to
        `reverse = not for_pagination and since is not None` so that pagination
        always walks BACKWARD (older messages per page).
        """
        from telegram_lib.messages import read_messages

        client = _mock_client()
        client.get_entity = AsyncMock(return_value=_mock_entity())
        client.get_messages = AsyncMock(return_value=[])

        await read_messages(client, 123, since=SINCE, for_pagination=True)

        call_kwargs = client.get_messages.call_args
        assert call_kwargs.kwargs.get("reverse") is False, (
            "for_pagination=True must call get_messages with reverse=False "
            "(backward/older-first direction); got reverse=True which walks forward "
            "and re-fetches the same newest messages on every page."
        )


# -----------------------------------------------------------------------
# F2 — send_message
# -----------------------------------------------------------------------


class TestSendMessage:
    """F2: send a message under the user's account."""

    @pytest.mark.asyncio
    async def test_send_message_happy(self):
        from telegram_lib.messages import send_message

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
        from telegram_lib.messages import send_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ValueError("entity not found"))

        result = await send_message(client, 999, "Hi")

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND

    @pytest.mark.asyncio
    async def test_send_message_no_conn(self):
        from telegram_lib.messages import send_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ConnectionError("no network"))

        result = await send_message(client, 123, "Hi")

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_send_message_perm_deny(self):
        from telethon.errors import ChatWriteForbiddenError

        from telegram_lib.messages import send_message

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.send_message = AsyncMock(side_effect=ChatWriteForbiddenError(request=None))

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
        from telegram_lib.messages import edit_message

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
        from telegram_lib.messages import edit_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        result = await edit_message(client, 999, 1, "New")

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND

    @pytest.mark.asyncio
    async def test_edit_message_no_change(self):
        from telethon.errors import MessageNotModifiedError

        from telegram_lib.messages import edit_message

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.edit_message = AsyncMock(side_effect=MessageNotModifiedError(request=None))

        result = await edit_message(client, 123, 1, "Same text")

        assert not result.ok
        assert result.error.code == ErrorCode.NOT_MODIFIED

    @pytest.mark.asyncio
    async def test_edit_message_no_conn(self):
        from telegram_lib.messages import edit_message

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
        from telegram_lib.messages import delete_message

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
        from telegram_lib.messages import delete_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        result = await delete_message(client, 999, [1])

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_message_no_conn(self):
        from telegram_lib.messages import delete_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ConnectionError("no network"))

        result = await delete_message(client, 123, [1])

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_delete_message_perm_deny(self):
        from telethon.errors import MessageDeleteForbiddenError

        from telegram_lib.messages import delete_message

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.delete_messages = AsyncMock(side_effect=MessageDeleteForbiddenError(request=None))

        result = await delete_message(client, 123, [1])

        assert not result.ok
        assert result.error.code == ErrorCode.PERMISSION_DENIED


# -----------------------------------------------------------------------
# F10 — count_messages
# -----------------------------------------------------------------------


class TestCountMessages:
    """F10: count messages without downloading content."""

    @pytest.mark.asyncio
    async def test_count_messages_happy(self):
        from telegram_lib.messages import count_messages

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)

        total_list = MagicMock()
        total_list.total = 4200
        client.get_messages = AsyncMock(return_value=total_list)

        result = await count_messages(client, 123)

        assert result.ok
        assert result.payload == 4200
        client.get_messages.assert_called_once_with(entity, limit=0, offset_date=None)

    @pytest.mark.asyncio
    async def test_count_messages_since(self):
        from telegram_lib.messages import count_messages

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)

        total_list = MagicMock()
        total_list.total = 150
        client.get_messages = AsyncMock(return_value=total_list)

        result = await count_messages(client, 123, since=SINCE)

        assert result.ok
        assert result.payload == 150
        client.get_messages.assert_called_once_with(entity, limit=0, offset_date=SINCE)

    @pytest.mark.asyncio
    async def test_count_messages_not_found(self):
        from telegram_lib.messages import count_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        result = await count_messages(client, 999)

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND

    @pytest.mark.asyncio
    async def test_count_messages_no_conn(self):
        from telegram_lib.messages import count_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ConnectionError("no network"))

        result = await count_messages(client, 123)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_count_messages_timeout(self):
        from telegram_lib.messages import count_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=TimeoutError("timed out"))

        result = await count_messages(client, 123)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_count_messages_rate_limit(self):
        from telethon.errors import FloodWaitError

        from telegram_lib.messages import count_messages

        client = _mock_client()
        entity = _mock_entity()
        client.get_entity = AsyncMock(return_value=entity)
        client.get_messages = AsyncMock(side_effect=FloodWaitError(request=None, capture=20))

        result = await count_messages(client, 123)

        assert not result.ok
        assert result.error.code == ErrorCode.RATE_LIMITED
        assert result.error.retry_after == 20.0
