"""
Unit tests for telegram-cli timeout handling.

Verifies that when a Telegram API call times out (asyncio.TimeoutError),
the library returns a NETWORK_ERROR so the CLI can report it properly.

No credentials or network needed.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

import sys
from pathlib import Path

from telegram_lib.models import ErrorCode


def _mock_client():
    client = AsyncMock()
    client.is_connected.return_value = True
    return client


class TestTimeout:
    """Verify that asyncio.TimeoutError is handled as NETWORK_ERROR."""

    @pytest.mark.asyncio
    async def test_ping_timeout_returns_network_error(self):
        """ping must report NETWORK_ERROR when the connection times out."""
        from telegram_lib.health import check_availability

        client = _mock_client()
        client.get_me = AsyncMock(side_effect=asyncio.TimeoutError())

        result = await check_availability(client)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_get_dialogs_timeout_returns_network_error(self):
        """get-dialogs must report an error when the connection times out."""
        from telegram_lib.dialogs import get_dialogs

        client = _mock_client()

        async def _iter_timeout(limit=100):
            raise asyncio.TimeoutError()
            yield  # noqa: E501 — make it an async generator

        client.iter_dialogs = _iter_timeout

        result = await get_dialogs(client)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_read_messages_timeout(self):
        """backup (read_messages) must handle timeout gracefully."""
        from telegram_lib.messages import read_messages

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=asyncio.TimeoutError())

        result = await read_messages(client, 123)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_send_message_timeout(self):
        """send must handle timeout gracefully."""
        from telegram_lib.messages import send_message

        client = _mock_client()
        client.get_entity = AsyncMock(side_effect=asyncio.TimeoutError())

        result = await send_message(client, 123, "Hello")

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR
