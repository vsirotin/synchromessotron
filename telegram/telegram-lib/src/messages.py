"""
Message functions — read, send, edit, delete, count (F1–F4, F10).

All functions are stateless wrappers around Telethon calls.
Each returns ``TgResult`` with a typed payload or a ``TgError`` (T3, T6).
"""

from __future__ import annotations

from datetime import datetime

from telethon import TelegramClient

from src._logging import logged
from src.dialogs import _map_exception
from src.models import ErrorCode, MessageInfo, TgError, TgResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_message_info(msg, dialog_id: int) -> MessageInfo:
    """Convert a Telethon ``Message`` to a lightweight ``MessageInfo`` (T7)."""
    sender_name = None
    sender_id = None
    if msg.sender:
        sender_id = msg.sender_id
        sender_name = (
            getattr(msg.sender, "first_name", None)
            or getattr(msg.sender, "title", None)
        )
    return MessageInfo(
        id=msg.id,
        dialog_id=dialog_id,
        text=msg.message or "",
        date=msg.date,
        sender_id=sender_id,
        sender_name=sender_name,
        has_media=msg.media is not None,
        media_type=type(msg.media).__name__ if msg.media else None,
    )


# ---------------------------------------------------------------------------
# F1 — Read messages (full / incremental)
# ---------------------------------------------------------------------------


@logged
async def read_messages(
    client: TelegramClient,
    dialog_id: int | str,
    *,
    since: datetime | None = None,
    limit: int = 100,
) -> TgResult[list[MessageInfo]]:
    """Read messages from a dialog, optionally since a given timestamp (F1).

    When *since* is provided only messages strictly **after** that timestamp
    are returned (incremental backup).  When omitted the most recent *limit*
    messages are returned (full history page).

    Args:
        client: An authenticated ``TelegramClient``.
        dialog_id: Numeric dialog ID or string handle (e.g. ``"me"``).
        since: If set, only return messages posted after this timestamp.
        limit: Maximum number of messages to return per call.

    Returns:
        ``TgResult`` whose payload is a list of ``MessageInfo``.

    Possible errors (``TgResult.error``):
        - ``ENTITY_NOT_FOUND`` — dialog_id does not resolve to a known entity.
        - ``NETWORK_ERROR`` — connection lost or timed out.
        - ``RATE_LIMITED`` — Telegram flood-wait; ``retry_after`` is populated.
        - ``SESSION_INVALID`` — session string is invalid or revoked.
        - ``AUTH_FAILED`` — user account is deactivated or banned.
        - ``INTERNAL_ERROR`` — unexpected / unmapped exception.
    """
    try:
        entity = await client.get_entity(dialog_id)
        raw_messages = await client.get_messages(
            entity,
            limit=limit,
            offset_date=since,
            reverse=since is not None,
        )
        result: list[MessageInfo] = []
        peer_id = _resolve_peer_id(entity)
        for msg in raw_messages:
            if since and msg.date <= since:
                continue
            result.append(_to_message_info(msg, peer_id))
        return TgResult(payload=result)
    except ValueError as exc:
        return TgResult(error=TgError(ErrorCode.ENTITY_NOT_FOUND, str(exc)))
    except Exception as exc:
        return TgResult(error=_map_exception(exc))


# ---------------------------------------------------------------------------
# F2 — Send a message
# ---------------------------------------------------------------------------


@logged
async def send_message(
    client: TelegramClient,
    dialog_id: int | str,
    text: str,
) -> TgResult[MessageInfo]:
    """Send a text message to a dialog on behalf of the user (F2).

    Args:
        client: An authenticated ``TelegramClient``.
        dialog_id: Target dialog (numeric ID or string handle).
        text: The message text to send.

    Returns:
        ``TgResult`` whose payload is the sent ``MessageInfo``.

    Possible errors (``TgResult.error``):
        - ``ENTITY_NOT_FOUND`` — dialog_id does not resolve to a known entity.
        - ``PERMISSION_DENIED`` — user cannot write to this chat.
        - ``NETWORK_ERROR`` — connection lost or timed out.
        - ``RATE_LIMITED`` — Telegram flood-wait; ``retry_after`` is populated.
        - ``SESSION_INVALID`` — session string is invalid or revoked.
        - ``INTERNAL_ERROR`` — unexpected / unmapped exception.
    """
    try:
        entity = await client.get_entity(dialog_id)
        msg = await client.send_message(entity, text)
        peer_id = _resolve_peer_id(entity)
        return TgResult(payload=_to_message_info(msg, peer_id))
    except ValueError as exc:
        return TgResult(error=TgError(ErrorCode.ENTITY_NOT_FOUND, str(exc)))
    except Exception as exc:
        return TgResult(error=_map_exception(exc))


# ---------------------------------------------------------------------------
# F3 — Edit own message
# ---------------------------------------------------------------------------


@logged
async def edit_message(
    client: TelegramClient,
    dialog_id: int | str,
    message_id: int,
    new_text: str,
) -> TgResult[MessageInfo]:
    """Edit a previously sent message (F3).

    Only messages sent by the authenticated user can be edited.

    Args:
        client: An authenticated ``TelegramClient``.
        dialog_id: The dialog containing the message.
        message_id: ID of the message to edit.
        new_text: The replacement text.

    Returns:
        ``TgResult`` whose payload is the updated ``MessageInfo``.

    Possible errors (``TgResult.error``):
        - ``ENTITY_NOT_FOUND`` — dialog or message not found.
        - ``NOT_MODIFIED`` — new text is identical to current text.
        - ``PERMISSION_DENIED`` — user is not the author of the message.
        - ``NETWORK_ERROR`` — connection lost or timed out.
        - ``RATE_LIMITED`` — Telegram flood-wait; ``retry_after`` is populated.
        - ``INTERNAL_ERROR`` — unexpected / unmapped exception.
    """
    try:
        entity = await client.get_entity(dialog_id)
        msg = await client.edit_message(entity, message_id, new_text)
        peer_id = _resolve_peer_id(entity)
        return TgResult(payload=_to_message_info(msg, peer_id))
    except ValueError as exc:
        return TgResult(error=TgError(ErrorCode.ENTITY_NOT_FOUND, str(exc)))
    except Exception as exc:
        return TgResult(error=_map_exception(exc))


# ---------------------------------------------------------------------------
# F4 — Delete own message
# ---------------------------------------------------------------------------


@logged
async def delete_message(
    client: TelegramClient,
    dialog_id: int | str,
    message_ids: list[int],
) -> TgResult[list[int]]:
    """Delete one or more of the user's own messages (F4).

    Args:
        client: An authenticated ``TelegramClient``.
        dialog_id: The dialog containing the messages.
        message_ids: IDs of the messages to delete.

    Returns:
        ``TgResult`` whose payload is the list of deleted message IDs.

    Possible errors (``TgResult.error``):
        - ``ENTITY_NOT_FOUND`` — dialog not found.
        - ``PERMISSION_DENIED`` — user cannot delete these messages.
        - ``NETWORK_ERROR`` — connection lost or timed out.
        - ``RATE_LIMITED`` — Telegram flood-wait; ``retry_after`` is populated.
        - ``INTERNAL_ERROR`` — unexpected / unmapped exception.
    """
    try:
        entity = await client.get_entity(dialog_id)
        await client.delete_messages(entity, message_ids)
        return TgResult(payload=message_ids)
    except ValueError as exc:
        return TgResult(error=TgError(ErrorCode.ENTITY_NOT_FOUND, str(exc)))
    except Exception as exc:
        return TgResult(error=_map_exception(exc))


# ---------------------------------------------------------------------------
# F10 — Count messages (lightweight metadata query)
# ---------------------------------------------------------------------------


@logged
async def count_messages(
    client: TelegramClient,
    dialog_id: int | str,
    *,
    since: datetime | None = None,
) -> TgResult[int]:
    """Return the total number of messages in a dialog without downloading content (F10).

    This is a lightweight metadata query that uses Telethon's
    ``client.get_messages(entity, limit=0)`` which returns a ``TotalList``
    with ``.total`` — the server-side message count — without fetching
    any message bodies.

    When *since* is provided, only messages strictly **after** that
    timestamp are counted (using ``offset_date``).

    Args:
        client: An authenticated ``TelegramClient``.
        dialog_id: Numeric dialog ID or string handle (e.g. ``"me"``).
        since: If set, count only messages posted after this timestamp.

    Returns:
        ``TgResult`` whose payload is an ``int`` — the message count.

    Possible errors (``TgResult.error``):
        - ``ENTITY_NOT_FOUND`` — dialog_id does not resolve to a known entity.
        - ``NETWORK_ERROR`` — connection lost or timed out.
        - ``RATE_LIMITED`` — Telegram flood-wait; ``retry_after`` is populated.
        - ``SESSION_INVALID`` — session string is invalid or revoked.
        - ``AUTH_FAILED`` — user account is deactivated or banned.
        - ``INTERNAL_ERROR`` — unexpected / unmapped exception.
    """
    try:
        entity = await client.get_entity(dialog_id)
        result = await client.get_messages(entity, limit=0, offset_date=since)
        return TgResult(payload=result.total)
    except ValueError as exc:
        return TgResult(error=TgError(ErrorCode.ENTITY_NOT_FOUND, str(exc)))
    except Exception as exc:
        return TgResult(error=_map_exception(exc))


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _resolve_peer_id(entity) -> int:
    """Extract a stable numeric ID from a Telethon entity."""
    return getattr(entity, "id", 0)
