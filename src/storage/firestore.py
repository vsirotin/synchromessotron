"""
Firestore-backed sync-state storage.

Stores and retrieves the last-sync timestamp from a Firestore document.
The collection name and document ID are configurable.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from google.cloud.firestore_v1.async_client import AsyncClient

from src.core.interfaces import ISyncStateStorage

logger = logging.getLogger(__name__)

_DEFAULT_COLLECTION = "synchromessotron"
_DEFAULT_DOCUMENT = "state"
_FIELD = "timestamp"


class FirestoreStateStorage(ISyncStateStorage):
    """
    Persists the last-sync timestamp in a single Firestore document.

    Document path: ``{collection}/{document}``
    Document schema: ``{ "timestamp": <Firestore Timestamp> }``
    """

    def __init__(
        self,
        client: AsyncClient,
        collection: str = _DEFAULT_COLLECTION,
        document: str = _DEFAULT_DOCUMENT,
    ) -> None:
        self._doc_ref = client.collection(collection).document(document)

    async def get_last_sync(self) -> datetime:
        snapshot = await self._doc_ref.get()
        if snapshot.exists and _FIELD in snapshot.to_dict():
            ts = snapshot.to_dict()[_FIELD]
            # Firestore timestamps expose .replace for tzinfo normalization
            dt: datetime = ts if isinstance(ts, datetime) else ts.datetime
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            logger.debug("Retrieved last sync: %s", dt)
            return dt

        # First run: return epoch so that no messages are missed.
        logger.info("No last-sync record found. Defaulting to epoch.")
        return datetime.fromtimestamp(0, tz=UTC)

    async def set_last_sync(self, dt: datetime) -> None:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        await self._doc_ref.set({_FIELD: dt})
        logger.debug("Persisted last sync: %s", dt)
