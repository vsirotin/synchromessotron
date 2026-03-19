"""
Unit tests for src/health.py — check_availability (F7), validate_session (F8).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_lib.models import ErrorCode


def _mock_client():
    client = AsyncMock()
    client.is_connected.return_value = True
    return client


# -----------------------------------------------------------------------
# F7 — check_availability
# -----------------------------------------------------------------------


class TestCheckAvailability:
    """F7: verify Telegram is reachable."""

    @pytest.mark.asyncio
    async def test_check_avail_happy(self):
        from telegram_lib.health import check_availability

        client = _mock_client()
        client.is_connected = MagicMock(return_value=True)
        client.get_me = AsyncMock(return_value=MagicMock())

        result = await check_availability(client)

        assert result.ok
        assert result.payload.available is True
        assert result.payload.latency_ms is not None

    @pytest.mark.asyncio
    async def test_check_avail_no_conn(self):
        from telegram_lib.health import check_availability

        client = _mock_client()
        client.is_connected = MagicMock(return_value=True)
        client.get_me = AsyncMock(side_effect=ConnectionError("unreachable"))

        result = await check_availability(client)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_check_avail_reconn(self):
        """Branch: client is not connected, so connect() is called first."""
        from telegram_lib.health import check_availability

        client = _mock_client()
        client.is_connected = MagicMock(return_value=False)
        client.connect = AsyncMock()
        client.get_me = AsyncMock(return_value=MagicMock())

        result = await check_availability(client)

        assert result.ok
        assert result.payload.available is True
        client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_avail_timeout(self):
        from telegram_lib.health import check_availability

        client = _mock_client()
        client.is_connected = MagicMock(return_value=True)
        client.get_me = AsyncMock(side_effect=TimeoutError("timed out"))

        result = await check_availability(client)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR


# -----------------------------------------------------------------------
# F8 — validate_session
# -----------------------------------------------------------------------


class TestValidateSession:
    """F8: validate the current session."""

    @pytest.mark.asyncio
    async def test_validate_sess_happy(self):
        from telegram_lib.health import validate_session

        me = MagicMock()
        me.id = 12345
        me.first_name = "Viktor"
        me.last_name = "S"
        me.username = "vsirotin"
        me.phone = "+1234567890"

        client = _mock_client()
        client.get_me = AsyncMock(return_value=me)

        result = await validate_session(client)

        assert result.ok
        assert result.payload.valid is True
        assert result.payload.user_id == 12345
        assert result.payload.username == "vsirotin"

    @pytest.mark.asyncio
    async def test_validate_sess_invalid(self):
        """get_me returns None when the session is not authenticated."""
        from telegram_lib.health import validate_session

        client = _mock_client()
        client.get_me = AsyncMock(return_value=None)

        result = await validate_session(client)

        assert not result.ok
        assert result.error.code == ErrorCode.SESSION_INVALID

    @pytest.mark.asyncio
    async def test_validate_sess_no_conn(self):
        from telegram_lib.health import validate_session

        client = _mock_client()
        client.get_me = AsyncMock(side_effect=ConnectionError("no network"))

        result = await validate_session(client)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_validate_sess_timeout(self):
        from telegram_lib.health import validate_session

        client = _mock_client()
        client.get_me = AsyncMock(side_effect=TimeoutError("timed out"))

        result = await validate_session(client)

        assert not result.ok
        assert result.error.code == ErrorCode.NETWORK_ERROR
