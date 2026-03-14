"""
Telegram Reader — reads messages from a Telegram dialog using Telethon.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession

from src.core.interfaces import IReader, Message, MessengerAccount

logger = logging.getLogger(__name__)


def _load_credentials(credentials_ref: str) -> tuple[int, str, str]:
    """Load Telegram credentials from an env var.

    Expected JSON: ``{"api_id": 12345, "api_hash": "...", "session": "..."}``
    """
    raw = os.environ.get(credentials_ref)
    if not raw:
        raise OSError(
            f"Environment variable {credentials_ref!r} is not set. "
            "Expected JSON with keys: api_id, api_hash, session."
        )
    data = json.loads(raw)
    return int(data["api_id"]), str(data["api_hash"]), str(data["session"])


def _map_message(msg, peer_id: str) -> Message:
    return Message(
        id=str(msg.id),
        text=msg.message or "",
        timestamp=msg.date,
        source_messenger="telegram",
        metadata={"peer_id": peer_id, "message_id": msg.id},
    )


class TelegramReader(IReader):
    """Reads new messages from a Telegram dialog using a Telethon user-level session."""

    async def read_since(
        self, account: MessengerAccount, since: datetime
    ) -> list[Message]:
        api_id, api_hash, session_string = _load_credentials(account.credentials_ref)
        async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
            messages: list[Message] = []
            try:
                async for msg in client.iter_messages(
                    account.account_id,
                    reverse=True,
                    offset_date=since,
                ):
                    if msg.date <= since:
                        continue
                    if msg.message or msg.media:
                        messages.append(_map_message(msg, account.account_id))
            except FloodWaitError as exc:
                logger.warning(
                    "Telegram rate limit: must wait %d seconds.", exc.seconds
                )
                await asyncio.sleep(exc.seconds)
                raise OSError(f"Telegram rate limit: retry after {exc.seconds}s") from exc

        logger.debug(
            "Read %d message(s) from Telegram peer %s",
            len(messages),
            account.account_id,
        )
        return messages
