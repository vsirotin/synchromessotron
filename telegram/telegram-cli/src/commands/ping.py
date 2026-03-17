"""
Ping command (F7) — check Telegram availability.
"""

from __future__ import annotations

import asyncio

from src.config import load_config
from src._lib import create_client, check_availability
from src.errors import format_error_and_exit


def run_ping() -> None:
    """Load config, ping Telegram, and print the result."""
    config = load_config()
    client = create_client(config["api_id"], config["api_hash"], config["session"])
    result = asyncio.run(_ping(client))

    if not result.ok:
        format_error_and_exit(result.error)

    latency = result.payload.latency_ms
    print(f"✓ Telegram is reachable ({latency} ms)")


async def _ping(client):
    """Connect, check availability, disconnect."""
    async with client:
        return await check_availability(client)
