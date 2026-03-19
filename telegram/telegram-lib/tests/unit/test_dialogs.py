"""
Unit tests for src/dialogs.py — get_dialogs (F5).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_lib.models import ErrorCode


def _mock_client():
    client = AsyncMock()
    client.is_connected.return_value = True
    return client


class TestGetDialogs:
    """F5: retrieve the user's dialog list."""

    @pytest.mark.asyncio
    async def test_get_dialogs_happy(self):
        from telegram_lib.dialogs import get_dialogs

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
    async def test_get_dialogs_no_conn(self):
        from telegram_lib.dialogs import get_dialogs

        client = _mock_client()

        async def _iter_dialogs(limit=100):
            raise ConnectionError("no network")
            yield  # make it an async generator  # noqa: E501

        client.iter_dialogs = _iter_dialogs

        result = await get_dialogs(client)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_get_dialogs_timeout(self):
        from telegram_lib.dialogs import get_dialogs

        client = _mock_client()

        async def _iter_dialogs(limit=100):
            raise TimeoutError("connection timed out")
            yield  # noqa: E501

        client.iter_dialogs = _iter_dialogs

        result = await get_dialogs(client)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_get_dialogs_rate_limit(self):
        from telethon.errors import FloodWaitError

        from telegram_lib.dialogs import get_dialogs

        client = _mock_client()

        exc = FloodWaitError(request=None, capture=30)

        async def _iter_dialogs(limit=100):
            raise exc
            yield  # noqa: E501

        client.iter_dialogs = _iter_dialogs

        result = await get_dialogs(client)

        assert not result.ok
        assert result.error.code == ErrorCode.RATE_LIMITED
        assert result.error.retry_after == 30.0

    @pytest.mark.asyncio
    async def test_get_dialogs_empty(self):
        from telegram_lib.dialogs import get_dialogs

        client = _mock_client()

        async def _iter_dialogs(limit=100):
            return
            yield  # noqa: E501

        client.iter_dialogs = _iter_dialogs

        result = await get_dialogs(client)

        assert result.ok
        assert result.payload == []
