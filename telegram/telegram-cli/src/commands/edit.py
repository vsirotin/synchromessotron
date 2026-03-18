"""
Edit command (F3) — edit a previously sent message.
"""

from __future__ import annotations

import asyncio
import json
import logging

from src.config import load_config
from src._lib import create_client, edit_message
from src.errors import format_error_and_exit

logger = logging.getLogger("telegram_cli")


def run_edit(*, dialog_id: int, message_id: int, text: str) -> None:
    """Load config, edit message, and print updated message as JSON."""
    config = load_config()
    client = create_client(config["api_id"], config["api_hash"], config["session"])
    result = asyncio.run(_edit(client, dialog_id, message_id, text))

    if not result.ok:
        format_error_and_exit(result.error)

    msg = result.payload
    output = {
        "id": msg.id,
        "date": msg.date.isoformat(),
        "text": msg.text,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


async def _edit(client, dialog_id, message_id, text):
    """Connect, edit, disconnect."""
    async with client:
        return await edit_message(client, dialog_id, message_id, text)
