"""
Members function — retrieve dialog participants (F1 supplementary).

Retrieves the list of members in a dialog (group or channel).
Returns ``TgResult`` with a list of ``MemberInfo`` objects (T6).
"""

from __future__ import annotations

from dataclasses import dataclass

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User

from telegram_lib._logging import logged
from telegram_lib.dialogs import _map_exception
from telegram_lib.models import ErrorCode, TgError, TgResult


@dataclass(frozen=True)
class MemberInfo:
    """Basic information about a dialog member."""

    id: int
    name: str
    username: str | None = None
    photo_file_path: str | None = None


# ---------------------------------------------------------------------------
# Get members
# ---------------------------------------------------------------------------


@logged
async def get_members(
    client: TelegramClient,
    dialog_id: int | str,
) -> TgResult[list[MemberInfo]]:
    """Retrieve the list of members in a dialog (group or channel).

    Args:
        client: An authenticated ``TelegramClient``.
        dialog_id: The dialog ID (group or channel).

    Returns:
        ``TgResult`` whose payload is a list of ``MemberInfo`` objects.

    Possible errors (``TgResult.error``):
        - ``ENTITY_NOT_FOUND`` — dialog not found or is not a group/channel.
        - ``PERMISSION_DENIED`` — no permission to access members list.
        - ``NETWORK_ERROR`` — connection lost or timed out.
        - ``RATE_LIMITED`` — Telegram flood-wait; ``retry_after`` is populated.
        - ``SESSION_INVALID`` — session string is invalid or revoked.
    """
    try:
        entity = await client.get_entity(dialog_id)

        # Check if entity is a group or channel (has members)
        if isinstance(entity, User):
            return TgResult(
                error=TgError(
                    ErrorCode.ENTITY_NOT_FOUND,
                    "Cannot retrieve members from a private user chat",
                )
            )

        if not isinstance(entity, (Chat, Channel)):
            return TgResult(
                error=TgError(
                    ErrorCode.ENTITY_NOT_FOUND,
                    "Dialog is not a group or channel",
                )
            )

        members: list[MemberInfo] = []
        try:
            async for member in client.iter_participants(entity):
                user = member.username if hasattr(member, "username") else None
                name = ""

                # Build name from first_name and last_name
                if hasattr(member, "first_name") and member.first_name:
                    name = member.first_name
                if hasattr(member, "last_name") and member.last_name:
                    name = f"{name} {member.last_name}".strip()

                # If no name, use username or ID as fallback
                if not name:
                    name = user or f"User {member.id}"

                members.append(
                    MemberInfo(
                        id=member.id,
                        name=name.strip(),
                        username=user,
                        photo_file_path=None,  # Could add photo download later
                    )
                )
        except Exception as exc:
            # If we can't iterate members due to permissions, return empty list
            if "CHANNELS_TOO_LARGE" in str(exc) or "USER_PRIVACY_RESTRICTED" in str(exc):
                return TgResult(payload=[])
            raise

        return TgResult(payload=members)
    except ValueError as exc:
        return TgResult(error=TgError(ErrorCode.ENTITY_NOT_FOUND, str(exc)))
    except Exception as exc:
        return TgResult(error=_map_exception(exc))
