"""
Unit tests for src/media.py — download_media (F6).
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models import ErrorCode

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
    return e


def _mock_client():
    client = AsyncMock()
    client.is_connected.return_value = True
    return client


class TestDownloadMedia:
    """F6: download photos and media files."""

    @pytest.mark.asyncio
    async def test_download_media_happy(self, tmp_path):
        from src.media import download_media

        # Create a fake downloaded file
        fake_file = tmp_path / "photo.jpg"
        fake_file.write_bytes(b"\xff\xd8fake-jpeg-data")

        media_mock = MagicMock()
        media_mock.mime_type = "image/jpeg"
        msg = _make_tg_msg(media=media_mock)

        client = _mock_client()
        client.get_entity = AsyncMock(return_value=_mock_entity())
        client.get_messages = AsyncMock(return_value=[msg])
        client.download_media = AsyncMock(return_value=str(fake_file))

        result = await download_media(client, 123, 1, dest_dir=str(tmp_path))

        assert result.ok
        assert result.payload.message_id == 1
        assert result.payload.file_path == str(fake_file)
        assert result.payload.size_bytes == len(b"\xff\xd8fake-jpeg-data")

    @pytest.mark.asyncio
    async def test_download_media_no_media(self):
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
    async def test_download_media_msg_miss(self):
        from src.media import download_media

        client = _mock_client()
        client.get_entity = AsyncMock(return_value=_mock_entity())
        client.get_messages = AsyncMock(return_value=[None])

        result = await download_media(client, 123, 999)

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND

    @pytest.mark.asyncio
    async def test_download_media_not_found(self):
        from src.media import download_media

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ValueError("entity not found"))

        result = await download_media(client, 999, 1)

        assert not result.ok
        assert result.error.code == ErrorCode.ENTITY_NOT_FOUND

    @pytest.mark.asyncio
    async def test_download_media_no_conn(self):
        from src.media import download_media

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=ConnectionError("no network"))

        result = await download_media(client, 123, 1)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_download_media_null_path(self):
        from src.media import download_media

        media_mock = MagicMock()
        msg = _make_tg_msg(media=media_mock)

        client = _mock_client()
        client.get_entity = AsyncMock(return_value=_mock_entity())
        client.get_messages = AsyncMock(return_value=[msg])
        client.download_media = AsyncMock(return_value=None)

        result = await download_media(client, 123, 1)

        assert not result.ok
        assert result.error.code == ErrorCode.INTERNAL_ERROR
