"""
Send command (F2) — send a text message to a dialog.
"""

from __future__ import annotations

import asyncio
import json
import logging

from src.config import load_config
from src._lib import create_client, send_message
from src.errors import format_error_and_exit

logger = logging.getLogger("telegram_cli")


def run_send(*, dialog_id: int, text: str) -> None:
    """Load config, send message, and print result as JSON."""
    config = load_config()
    client = create_client(config["api_id"], config["api_hash"], config["session"])
    result = asyncio.run(_send(client, dialog_id, text))

    if not result.ok:
        format_error_and_exit(result.error)

    msg = result.payload
    output = {
        "id": msg.id,
        "date": msg.date.isoformat(),
        "text": msg.text,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


async def _send(client, dialog_id, text):
    """Connect, send, disconnect."""
    async with client:
        return await send_message(client, dialog_id, text)
