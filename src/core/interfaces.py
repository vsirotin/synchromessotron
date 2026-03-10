"""
Core abstractions for Synchromessotron.

All messenger integrations must implement the interfaces defined here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Attachment:
    """A non-text attachment on a message (photo, file, audio, etc.)."""

    type: str  # e.g. "photo", "video", "document"
    url: str | None = None
    raw: Any = None  # raw platform-specific payload, for passthrough forwarding


@dataclass
class Message:
    """Platform-agnostic representation of a single message."""

    id: str
    text: str
    timestamp: datetime
    source_messenger: str  # e.g. "telegram", "vk"
    attachments: list[Attachment] = field(default_factory=list)
    # platform-specific data (e.g. peer_id, message_id for forwarding)
    metadata: dict = field(default_factory=dict)


@dataclass
class MessengerAccount:
    """Identifies an account within a specific messenger."""

    messenger_id: str  # e.g. "telegram", "vk"
    account_id: str  # username, phone number, or numeric ID
    credentials_ref: str  # name of the env var or Secret Manager path holding credentials


class IReader(ABC):
    """Reads messages from a messenger account."""

    @abstractmethod
    async def read_since(
        self, account: MessengerAccount, since: datetime
    ) -> list[Message]:
        """Return all messages posted after *since* (exclusive)."""


class IWriter(ABC):
    """Writes messages to a messenger account."""

    @abstractmethod
    async def write(
        self, account: MessengerAccount, messages: list[Message]
    ) -> None:
        """Write *messages* to *account*. Called only when messages is non-empty."""


class ISyncStateStorage(ABC):
    """Persists the timestamp of the last successful synchronization."""

    @abstractmethod
    async def get_last_sync(self) -> datetime:
        """Return the timestamp of the last completed sync."""

    @abstractmethod
    async def set_last_sync(self, dt: datetime) -> None:
        """Persist *dt* as the new last-sync timestamp."""
