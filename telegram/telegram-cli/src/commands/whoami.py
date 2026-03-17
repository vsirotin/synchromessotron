"""
Whoami command (F8) — validate session and show user info.
"""

from __future__ import annotations

import asyncio

from src.config import load_config
from src._lib import create_client, validate_session
from src.errors import format_error_and_exit


def run_whoami() -> None:
    """Load config, validate session, and print user info."""
    config = load_config()
    client = create_client(config["api_id"], config["api_hash"], config["session"])
    result = asyncio.run(_whoami(client))

    if not result.ok:
        format_error_and_exit(result.error)

    info = result.payload
    name_parts = [info.first_name or ""]
    if info.last_name:
        name_parts.append(info.last_name)
    name = " ".join(name_parts).strip()

    print("✓ Session valid")
    print(f"  User ID:   {info.user_id}")
    print(f"  Name:      {name}")
    if info.username:
        print(f"  Username:  @{info.username}")
    if info.phone:
        print(f"  Phone:     +{info.phone}")


async def _whoami(client):
    """Connect, validate, disconnect."""
    async with client:
        return await validate_session(client)
