"""
VK Writer — sends or forwards messages to a VK.com conversation using vk_api.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging

import vk_api

from src.core.interfaces import IWriter, Message, MessengerAccount
from src.messengers.vk.reader import _load_credentials

logger = logging.getLogger(__name__)


def _random_id(peer_id: int, message_id: str, text: str) -> int:
    """Deterministic random_id for messages.send — safe to use on retries.

    VK requires a unique random_id per send call to prevent duplicate delivery.
    Using a hash makes the value stable across retries of the same message.
    Must fit in a 32-bit signed integer.
    """
    payload = f"{peer_id}:{message_id}:{text}"
    digest = hashlib.sha256(payload.encode()).digest()
    return int.from_bytes(digest[:4], "big", signed=True)


class VKWriter(IWriter):
    """Writes messages to a VK.com conversation.

    Strategies:
    - ``"forward"``: Natively forwards the message if it originated from VK.
                     Falls back to repost for cross-messenger messages.
    - ``"repost"``: Sends a new text message with an attribution prefix.
    """

    def __init__(self, strategy: str = "repost") -> None:
        self._strategy = strategy

    async def write(
        self, account: MessengerAccount, messages: list[Message]
    ) -> None:
        await asyncio.to_thread(self._write_sync, account, messages)

    def _write_sync(self, account: MessengerAccount, messages: list[Message]) -> None:
        token = _load_credentials(account.credentials_ref)
        session = vk_api.VkApi(token=token)
        vk = session.get_api()
        peer_id = int(account.account_id)
        for msg in messages:
            self._send_one(vk, peer_id, msg)

    def _send_one(self, vk, peer_id: int, msg: Message) -> None:
        rid = _random_id(peer_id, msg.id, msg.text)
        can_forward = (
            self._strategy == "forward"
            and msg.source_messenger == "vk"
            and "peer_id" in msg.metadata
            and "message_id" in msg.metadata
        )
        if can_forward:
            forward_params = json.dumps({
                "peer_id": msg.metadata["peer_id"],
                "message_ids": [msg.metadata["message_id"]],
                "is_reply": False,
            })
            vk.messages.send(peer_id=peer_id, forward=forward_params, random_id=rid)
            logger.debug("Forwarded VK message %s to peer %d", msg.id, peer_id)
        else:
            attribution = (
                f"[From {msg.source_messenger.capitalize()}]\n"
                if msg.source_messenger != "vk"
                else ""
            )
            vk.messages.send(peer_id=peer_id, message=attribution + msg.text, random_id=rid)
            logger.debug("Sent message to VK peer %d", peer_id)
