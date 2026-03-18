"""
Delete command (F4) — delete own messages.
"""

from __future__ import annotations

import asyncio
import json
import logging

from src.config import load_config
from src._lib import create_client, delete_message
from src.errors import format_error_and_exit

logger = logging.getLogger("telegram_cli")


def run_delete(*, dialog_id: int, message_ids: list[int]) -> None:
    """Load config, delete messages, and print deleted IDs."""
    config = load_config()
    client = create_client(config["api_id"], config["api_hash"], config["session"])
    result = asyncio.run(_delete(client, dialog_id, message_ids))

    if not result.ok:
        format_error_and_exit(result.error)

    print(json.dumps(result.payload))


async def _delete(client, dialog_id, message_ids):
    """Connect, delete, disconnect."""
    async with client:
        return await delete_message(client, dialog_id, message_ids)
