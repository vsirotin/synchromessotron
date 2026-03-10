"""
VK Reader — reads messages from a VK.com conversation using vk_api.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import UTC, datetime

import vk_api

from src.core.interfaces import IReader, Message, MessengerAccount

logger = logging.getLogger(__name__)

_PAGE_SIZE = 200


def _load_credentials(credentials_ref: str) -> str:
    """Load VK user token from an env var.

    Expected JSON: ``{"token": "vk_user_access_token"}``
    """
    raw = os.environ.get(credentials_ref)
    if not raw:
        raise OSError(
            f"Environment variable {credentials_ref!r} is not set. "
            "Expected JSON with key: token."
        )
    return json.loads(raw)["token"]


def _map_message(item: dict) -> Message:
    ts = datetime.fromtimestamp(item["date"], tz=UTC)
    return Message(
        id=str(item["id"]),
        text=item.get("text", ""),
        timestamp=ts,
        source_messenger="vk",
        metadata={"peer_id": item.get("peer_id"), "message_id": item["id"]},
    )


class VKReader(IReader):
    """Reads new messages from a VK.com conversation."""

    async def read_since(
        self, account: MessengerAccount, since: datetime
    ) -> list[Message]:
        return await asyncio.to_thread(self._read_sync, account, since)

    def _read_sync(self, account: MessengerAccount, since: datetime) -> list[Message]:
        token = _load_credentials(account.credentials_ref)
        session = vk_api.VkApi(token=token)
        vk = session.get_api()

        since_ts = since.timestamp()
        peer_id = int(account.account_id)
        messages: list[Message] = []
        offset = 0

        while True:
            response = vk.messages.getHistory(
                peer_id=peer_id,
                count=_PAGE_SIZE,
                offset=offset,
            )
            items = response.get("items", [])
            if not items:
                break

            # VK returns messages newest-first; stop once we pass the boundary.
            reached_boundary = False
            for item in items:
                if item["date"] > since_ts:
                    messages.append(_map_message(item))
                else:
                    reached_boundary = True
                    break

            if reached_boundary or len(items) < _PAGE_SIZE:
                break
            offset += _PAGE_SIZE

        messages.sort(key=lambda m: m.timestamp)
        logger.debug("Read %d message(s) from VK peer %d", len(messages), peer_id)
        return messages
