"""
Telegram Writer — sends or forwards messages to a Telegram dialog using Telethon.
"""

from __future__ import annotations

import asyncio
import logging

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession

from src.core.interfaces import IWriter, Message, MessengerAccount
from src.messengers.telegram.reader import _load_credentials

logger = logging.getLogger(__name__)


class TelegramWriter(IWriter):
    """Writes messages to a Telegram dialog.

    Strategies:
    - ``"forward"``: Natively forwards the message if it originated from Telegram.
                     Falls back to repost for cross-messenger messages.
    - ``"repost"``: Sends a new text message with an attribution prefix.
    """

    def __init__(self, strategy: str = "repost") -> None:
        self._strategy = strategy

    async def write(
        self, account: MessengerAccount, messages: list[Message]
    ) -> None:
        api_id, api_hash, session_string = _load_credentials(account.credentials_ref)
        async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
            for msg in messages:
                try:
                    await self._write_one(client, account.account_id, msg)
                except FloodWaitError as exc:
                    logger.warning("Telegram rate limit: waiting %d seconds.", exc.seconds)
                    await asyncio.sleep(exc.seconds)
                    await self._write_one(client, account.account_id, msg)

    async def _write_one(self, client, target_peer: str, msg: Message) -> None:
        can_forward = (
            self._strategy == "forward"
            and msg.source_messenger == "telegram"
            and "peer_id" in msg.metadata
            and "message_id" in msg.metadata
        )
        if can_forward:
            await client.forward_messages(
                target_peer,
                [msg.metadata["message_id"]],
                from_peer=msg.metadata["peer_id"],
            )
            logger.debug("Forwarded Telegram message %s to %s", msg.id, target_peer)
        else:
            attribution = (
                f"[From {msg.source_messenger.capitalize()}]\n"
                if msg.source_messenger != "telegram"
                else ""
            )
            await client.send_message(target_peer, attribution + msg.text)
            logger.debug("Sent message to Telegram peer %s", target_peer)
