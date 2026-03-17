"""
Telegram client factory (stateless helper).

Provides ``create_client()`` which builds a ready-to-use
``TelegramClient`` from a credentials dictionary.
The caller owns the client's lifecycle (connect / disconnect).
"""

from __future__ import annotations

import logging

from telethon import TelegramClient
from telethon.sessions import StringSession

logger = logging.getLogger("telegram_lib")


def create_client(
    api_id: int,
    api_hash: str,
    session: str = "",
) -> TelegramClient:
    """Create a Telethon ``TelegramClient`` from explicit credentials.

    This is a synchronous factory — no network I/O happens here.
    The caller is responsible for connecting and disconnecting the client.

    Args:
        api_id: Telegram application API ID.
        api_hash: Telegram application API hash.
        session: A session string previously obtained via ``generate_session.py``.
            Pass an empty string to start a new (unauthenticated) session.

    Returns:
        A ``TelegramClient`` instance.  Use it as an async context manager::

            client = create_client(api_id, api_hash, session)
            async with client:
                ...

    Note:
        This function does not raise exceptions.  Invalid credentials will
        cause errors later when the client attempts to connect.
    """
    logger.debug("create_client called | api_id=%s session_len=%d", api_id, len(session))
    client = TelegramClient(StringSession(session), api_id, api_hash)
    logger.debug("create_client completed")
    return client
