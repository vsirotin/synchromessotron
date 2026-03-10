"""Unit tests for SyncOrchestrator."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.interfaces import Message, MessengerAccount
from src.core.orchestrator import SyncOrchestrator, SyncPair

LAST_SYNC = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
MSG_A = Message(id="1", text="hello", timestamp=LAST_SYNC, source_messenger="a")
MSG_B = Message(id="2", text="world", timestamp=LAST_SYNC, source_messenger="b")

ACC_A = MessengerAccount(messenger_id="a", account_id="user_a", credentials_ref="CRED_A")
ACC_B = MessengerAccount(messenger_id="b", account_id="user_b", credentials_ref="CRED_B")


def _make_storage(last_sync: datetime = LAST_SYNC):
    storage = MagicMock()
    storage.get_last_sync = AsyncMock(return_value=last_sync)
    storage.set_last_sync = AsyncMock()
    return storage


def _make_pair(messages: list[Message] = None):
    reader = MagicMock()
    reader.read_since = AsyncMock(return_value=messages or [])
    writer = MagicMock()
    writer.write = AsyncMock()
    return SyncPair(reader=reader, source_account=ACC_A, writer=writer, target_account=ACC_B)


@pytest.mark.asyncio
async def test_sync_writes_messages_to_target():
    pair = _make_pair([MSG_A])
    storage = _make_storage()
    await SyncOrchestrator([pair]).run(storage)

    pair.reader.read_since.assert_called_once_with(ACC_A, LAST_SYNC)
    pair.writer.write.assert_called_once_with(ACC_B, [MSG_A])


@pytest.mark.asyncio
async def test_sync_skips_write_when_no_new_messages():
    pair = _make_pair([])
    storage = _make_storage()
    await SyncOrchestrator([pair]).run(storage)

    pair.writer.write.assert_not_called()


@pytest.mark.asyncio
async def test_sync_updates_last_sync_after_success():
    pair = _make_pair([MSG_A])
    storage = _make_storage()
    await SyncOrchestrator([pair]).run(storage)

    storage.set_last_sync.assert_called_once()
    called_with = storage.set_last_sync.call_args[0][0]
    assert isinstance(called_with, datetime)
    assert called_with.tzinfo is not None


@pytest.mark.asyncio
async def test_sync_does_not_update_last_sync_on_write_failure():
    pair = _make_pair([MSG_A])
    pair.writer.write = AsyncMock(side_effect=RuntimeError("write failed"))
    storage = _make_storage()

    with pytest.raises(RuntimeError, match="write failed"):
        await SyncOrchestrator([pair]).run(storage)

    storage.set_last_sync.assert_not_called()


@pytest.mark.asyncio
async def test_multiple_pairs_all_written():
    reader_a = MagicMock()
    reader_a.read_since = AsyncMock(return_value=[MSG_A])
    writer_a = MagicMock()
    writer_a.write = AsyncMock()

    reader_b = MagicMock()
    reader_b.read_since = AsyncMock(return_value=[MSG_B])
    writer_b = MagicMock()
    writer_b.write = AsyncMock()

    pair1 = SyncPair(reader=reader_a, source_account=ACC_A, writer=writer_b, target_account=ACC_B)
    pair2 = SyncPair(reader=reader_b, source_account=ACC_B, writer=writer_a, target_account=ACC_A)

    storage = _make_storage()
    await SyncOrchestrator([pair1, pair2]).run(storage)

    writer_b.write.assert_called_once_with(ACC_B, [MSG_A])
    writer_a.write.assert_called_once_with(ACC_A, [MSG_B])
    storage.set_last_sync.assert_called_once()


def test_orchestrator_requires_at_least_one_pair():
    with pytest.raises(ValueError):
        SyncOrchestrator([])
