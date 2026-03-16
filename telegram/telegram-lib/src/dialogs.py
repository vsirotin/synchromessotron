"""
Dialog listing functions (F5).

Terminology (T9):
    In the Telegram API the term **"dialog"** denotes any conversation the
    user is part of — a one-to-one chat with another user, a group, or a
    channel.  This is the official term used by the MTProto protocol and the
    Telethon library.  We preserve it here to stay consistent with the
    upstream documentation.
"""

from __future__ import annotations

from telethon import TelegramClient

from src._logging import logged
from src.models import DialogInfo, ErrorCode, TgError, TgResult

# ---------------------------------------------------------------------------
# F5 — Retrieve dialogs
# ---------------------------------------------------------------------------


@logged
async def get_dialogs(
    client: TelegramClient,
    *,
    limit: int = 100,
) -> TgResult[list[DialogInfo]]:
    """Return the user's Telegram dialogs with lightweight metadata (F5).

    A "dialog" in the Telegram API is any conversation the user participates
    in: a one-to-one user chat, a group, or a channel.

    Args:
        client: An authenticated ``TelegramClient`` (created via ``create_client``).
        limit: Maximum number of dialogs to fetch. Defaults to 100.

    Returns:
        ``TgResult`` whose payload is a list of ``DialogInfo`` objects,
        or an error if the call fails (T6).
    """
    try:
        dialogs: list[DialogInfo] = []
        async for d in client.iter_dialogs(limit=limit):
            entity = d.entity
            kind = type(entity).__name__
            username = getattr(entity, "username", None)
            dialogs.append(
                DialogInfo(
                    id=d.id,
                    name=d.name or "",
                    type=kind,
                    username=username,
                    unread_count=d.unread_count,
                )
            )
        return TgResult(payload=dialogs)
    except ConnectionError as exc:
        return TgResult(error=TgError(ErrorCode.NETWORK_ERROR, str(exc)))
    except Exception as exc:
        return TgResult(error=_map_exception(exc))


def _map_exception(exc: Exception) -> TgError:
    """Map a Telethon/network exception to a ``TgError``."""
    from telethon.errors import (
        AuthKeyUnregisteredError,
        FloodWaitError,
        UserDeactivatedBanError,
    )

    if isinstance(exc, FloodWaitError):
        return TgError(
            ErrorCode.RATE_LIMITED,
            f"Rate limited — retry after {exc.seconds}s",
            retry_after=float(exc.seconds),
        )
    if isinstance(exc, AuthKeyUnregisteredError):
        return TgError(ErrorCode.SESSION_INVALID, "Session is invalid or revoked")
    if isinstance(exc, UserDeactivatedBanError):
        return TgError(ErrorCode.AUTH_FAILED, "User account is deactivated or banned")
    return TgError(
        ErrorCode.INTERNAL_ERROR,
        str(exc),
        details={"exception_type": type(exc).__name__},
    )
