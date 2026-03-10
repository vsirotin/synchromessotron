"""
Integration tests for FirestoreStateStorage.

Requires the Firestore emulator to be running:
  firebase emulators:start --only firestore

Set the environment variable before running:
  export FIRESTORE_EMULATOR_HOST=localhost:8080
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from google.cloud.firestore_v1.async_client import AsyncClient

from src.storage.firestore import FirestoreStateStorage

EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST")

pytestmark = pytest.mark.skipif(
    not EMULATOR_HOST,
    reason="Firestore emulator not available (set FIRESTORE_EMULATOR_HOST)",
)


@pytest_asyncio.fixture
async def storage():
    import google.auth.credentials  # type: ignore

    class _AnonymousCreds(google.auth.credentials.AnonymousCredentials):
        pass

    client = AsyncClient(project="test-project", credentials=_AnonymousCreds())
    yield FirestoreStateStorage(client, collection="test_sync_state", document="test_last_sync")
    # Cleanup: delete the test document
    doc_ref = client.collection("test_sync_state").document("test_last_sync")
    await doc_ref.delete()


@pytest.mark.asyncio
async def test_get_last_sync_returns_epoch_when_no_record(storage):
    epoch = datetime.fromtimestamp(0, tz=UTC)
    result = await storage.get_last_sync()
    assert result == epoch


@pytest.mark.asyncio
async def test_set_and_get_last_sync_roundtrip(storage):
    ts = datetime(2026, 3, 10, 12, 0, 0, tzinfo=UTC)
    await storage.set_last_sync(ts)
    result = await storage.get_last_sync()
    assert result == ts


@pytest.mark.asyncio
async def test_set_last_sync_overwrites_previous(storage):
    first = datetime(2026, 1, 1, tzinfo=UTC)
    second = datetime(2026, 6, 1, tzinfo=UTC)
    await storage.set_last_sync(first)
    await storage.set_last_sync(second)
    result = await storage.get_last_sync()
    assert result == second
