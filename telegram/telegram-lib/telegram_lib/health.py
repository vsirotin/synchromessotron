"""
Health-check functions — availability and session validation (F7, F8).

These are lightweight probes that callers use before starting heavier
operations like backup or message sync.
"""

from __future__ import annotations

import time

from telethon import TelegramClient

from telegram_lib._logging import logged
from telegram_lib.dialogs import _map_exception
from telegram_lib.models import ErrorCode, ServiceStatus, SessionInfo, TgError, TgResult

# ---------------------------------------------------------------------------
# F7 — Check Telegram availability
# ---------------------------------------------------------------------------


@logged
async def check_availability(client: TelegramClient) -> TgResult[ServiceStatus]:
    """Check whether the Telegram service is reachable (F7).

    Connects (if needed), measures round-trip latency, and disconnects.

    Args:
        client: A ``TelegramClient`` (does not need to be authenticated).

    Returns:
        ``TgResult`` whose payload is a ``ServiceStatus``.

    Possible errors (``TgResult.error``):
        - ``NETWORK_ERROR`` — Telegram is not reachable.
        - ``SESSION_INVALID`` — session string is invalid or revoked.
        - ``AUTH_FAILED`` — user account is deactivated or banned.
        - ``INTERNAL_ERROR`` — unexpected / unmapped exception.
    """
    try:
        start = time.monotonic()
        if not client.is_connected():
            await client.connect()
        await client.get_me()
        latency = (time.monotonic() - start) * 1000
        return TgResult(payload=ServiceStatus(available=True, latency_ms=round(latency, 1)))
    except ConnectionError as exc:
        return TgResult(
            error=TgError(ErrorCode.NETWORK_ERROR, str(exc)),
        )
    except Exception as exc:
        return TgResult(error=_map_exception(exc))


# ---------------------------------------------------------------------------
# F8 — Validate session
# ---------------------------------------------------------------------------


@logged
async def validate_session(client: TelegramClient) -> TgResult[SessionInfo]:
    """Validate the current session and return basic user information (F8).

    Args:
        client: An authenticated ``TelegramClient``.

    Returns:
        ``TgResult`` whose payload is a ``SessionInfo`` if the session is
        valid.

    Possible errors (``TgResult.error``):
        - ``SESSION_INVALID`` — session is not authenticated or was revoked.
        - ``NETWORK_ERROR`` — connection lost or timed out.
        - ``AUTH_FAILED`` — user account is deactivated or banned.
        - ``INTERNAL_ERROR`` — unexpected / unmapped exception.
    """
    try:
        me = await client.get_me()
        if me is None:
            return TgResult(
                error=TgError(ErrorCode.SESSION_INVALID, "Session is not authenticated")
            )
        return TgResult(
            payload=SessionInfo(
                valid=True,
                user_id=me.id,
                first_name=me.first_name,
                last_name=me.last_name,
                username=me.username,
                phone=me.phone,
            )
        )
    except Exception as exc:
        return TgResult(error=_map_exception(exc))
