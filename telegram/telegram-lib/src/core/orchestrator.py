"""
Sync orchestrator — implements the 5-step synchronization algorithm.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from src.core.interfaces import IReader, ISyncStateStorage, IWriter, MessengerAccount
from src.core.retry import retry_async

logger = logging.getLogger(__name__)


@dataclass
class SyncPair:
    """
    Describes one directed sync link:
      - read new messages from *source_account* using *reader*
      - write them to *target_account* using *writer*
    """

    reader: IReader
    source_account: MessengerAccount
    writer: IWriter
    target_account: MessengerAccount


class SyncOrchestrator:
    """
    Orchestrates message synchronization across a set of sync pairs.

    The algorithm per run:
      1. Read *last_sync* timestamp from storage.
      2. For every pair, read new messages from the source since *last_sync*.
      3. For every pair, write those messages to the target.
      4. Update *last_sync* in storage — only if all reads and writes succeeded.
    """

    def __init__(self, pairs: list[SyncPair]) -> None:
        if not pairs:
            raise ValueError("At least one SyncPair is required.")
        self._pairs = pairs

    async def run(self, storage: ISyncStateStorage) -> None:
        last_sync = await storage.get_last_sync()
        logger.info("Starting sync run. Last sync: %s", last_sync)

        # Step 1 & 2: read all sources first so that a write failure on one pair
        # does not cause the other source to be re-read.
        messages_per_pair: list[tuple[SyncPair, list]] = []
        for pair in self._pairs:
            messages = await retry_async(
                pair.reader.read_since, pair.source_account, last_sync
            )
            logger.info(
                "Read %d message(s) from %s/%s",
                len(messages),
                pair.source_account.messenger_id,
                pair.source_account.account_id,
            )
            messages_per_pair.append((pair, messages))

        # Step 3: write to all targets.
        for pair, messages in messages_per_pair:
            if not messages:
                logger.debug(
                    "No new messages for %s/%s — skipping write.",
                    pair.target_account.messenger_id,
                    pair.target_account.account_id,
                )
                continue
            await retry_async(pair.writer.write, pair.target_account, messages)
            logger.info(
                "Wrote %d message(s) to %s/%s",
                len(messages),
                pair.target_account.messenger_id,
                pair.target_account.account_id,
            )

        # Step 4: persist new sync timestamp only after all writes succeed.
        now = datetime.now(tz=UTC)
        await storage.set_last_sync(now)
        logger.info("Sync run complete. New last-sync timestamp: %s", now)
