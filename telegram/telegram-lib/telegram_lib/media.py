"""
Media download function (F6).

Downloads photos, documents, videos, and other media files attached to
messages.  Returns ``TgResult`` with a ``MediaResult`` payload (T6, T7).
"""

from __future__ import annotations

from pathlib import Path

from telethon import TelegramClient

from telegram_lib._logging import logged
from telegram_lib.dialogs import _map_exception
from telegram_lib.models import ErrorCode, MediaResult, TgError, TgResult

# ---------------------------------------------------------------------------
# F6 — Download media
# ---------------------------------------------------------------------------


@logged
async def download_media(
    client: TelegramClient,
    dialog_id: int | str,
    message_id: int,
    *,
    dest_dir: str | Path = ".",
) -> TgResult[MediaResult]:
    """Download the media attached to a specific message (F6).

    Args:
        client: An authenticated ``TelegramClient``.
        dialog_id: The dialog containing the message.
        message_id: ID of the message whose media should be downloaded.
        dest_dir: Directory where the file will be saved. Defaults to cwd.

    Returns:
        ``TgResult`` whose payload is a ``MediaResult`` with the local file
        path, MIME type, and size.

    Possible errors (``TgResult.error``):
        - ``ENTITY_NOT_FOUND`` — dialog, message, or media not found.
        - ``INTERNAL_ERROR`` — download succeeded but returned no file path.
        - ``NETWORK_ERROR`` — connection lost or timed out.
        - ``RATE_LIMITED`` — Telegram flood-wait; ``retry_after`` is populated.
        - ``SESSION_INVALID`` — session string is invalid or revoked.
    """
    try:
        entity = await client.get_entity(dialog_id)
        messages = await client.get_messages(entity, ids=message_id)
        if not messages or not messages[0]:
            return TgResult(
                error=TgError(ErrorCode.ENTITY_NOT_FOUND, f"Message {message_id} not found")
            )

        msg = messages[0]
        if not msg.media:
            return TgResult(
                error=TgError(
                    ErrorCode.ENTITY_NOT_FOUND,
                    f"Message {message_id} has no media attached",
                )
            )

        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)

        # Try to download media - some messages may not have downloadable media
        try:
            file_path = await client.download_media(msg, file=str(dest))
        except TypeError:
            # Common error with certain message types that don't have downloadable media
            return TgResult(
                error=TgError(
                    ErrorCode.ENTITY_NOT_FOUND,
                    f"Message {message_id} media format not downloadable",
                )
            )
        except Exception as exc:
            # Catch any other errors
            return TgResult(
                error=TgError(
                    ErrorCode.ENTITY_NOT_FOUND,
                    f"Failed to download message {message_id} media: {type(exc).__name__}",
                )
            )

        if file_path is None:
            return TgResult(
                error=TgError(ErrorCode.INTERNAL_ERROR, "Download returned no file path")
            )

        p = Path(file_path)

        # Try to get mime type, but don't fail if there's an error
        mime_type = None
        try:
            mime_type = getattr(msg.media, "mime_type", None)
            if not mime_type:
                mime_type = getattr(getattr(msg.media, "document", None), "mime_type", None)
        except Exception:
            # If we can't get mime type, just use None
            pass

        return TgResult(
            payload=MediaResult(
                message_id=message_id,
                file_path=str(p),
                mime_type=mime_type,
                size_bytes=p.stat().st_size if p.exists() else None,
            )
        )
    except ValueError as exc:
        return TgResult(error=TgError(ErrorCode.ENTITY_NOT_FOUND, str(exc)))
    except Exception as exc:
        return TgResult(error=_map_exception(exc))
