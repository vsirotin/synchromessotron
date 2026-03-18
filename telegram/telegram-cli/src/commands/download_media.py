"""
Download-media command (F6) — download media from a specific message.
"""

from __future__ import annotations

import asyncio
import json
import logging

from src.config import load_config
from src._lib import create_client, download_media
from src.errors import format_error_and_exit

logger = logging.getLogger("telegram_cli")


def run_download_media(*, dialog_id: int, message_id: int, dest: str = ".") -> None:
    """Load config, download media, and print result as JSON."""
    config = load_config()
    client = create_client(config["api_id"], config["api_hash"], config["session"])
    result = asyncio.run(_download(client, dialog_id, message_id, dest))

    if not result.ok:
        format_error_and_exit(result.error)

    media = result.payload
    output = {
        "message_id": media.message_id,
        "file_path": media.file_path,
        "mime_type": media.mime_type,
        "size_bytes": media.size_bytes,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


async def _download(client, dialog_id, message_id, dest):
    """Connect, download, disconnect."""
    async with client:
        return await download_media(client, dialog_id, message_id, dest_dir=dest)
