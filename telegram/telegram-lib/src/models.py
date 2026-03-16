"""
Data models for telegram-lib.

Defines the Result/Error types (T3, T6) and lightweight payload DTOs (T7)
returned by the library's stateless functions.

Terminology note (T9):
    In the Telegram API a "dialog" is any conversation — a one-to-one chat
    with another user, a group, or a channel.  The term comes from the
    internal Telethon / MTProto layer and is preserved here to stay
    consistent with the upstream documentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Error codes
# ---------------------------------------------------------------------------

class ErrorCode(str, Enum):
    """Standardised error codes returned by telegram-lib (T3)."""

    RATE_LIMITED = "RATE_LIMITED"
    AUTH_FAILED = "AUTH_FAILED"
    SESSION_INVALID = "SESSION_INVALID"
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_MODIFIED = "NOT_MODIFIED"
    NETWORK_ERROR = "NETWORK_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# Result / Error container (T6)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TgError:
    """Error descriptor returned instead of a payload (T3, T6).

    Attributes:
        code: Machine-readable error code.
        message: Human-readable description.
        retry_after: Seconds the caller should wait before retrying
            (populated when ``code == RATE_LIMITED``).
        details: Optional additional context (e.g. original exception class).
    """

    code: ErrorCode
    message: str
    retry_after: float | None = None
    details: dict[str, Any] | None = None


@dataclass(frozen=True)
class TgResult(Generic[T]):
    """Either a *payload* **or** an *error* — never both (T6).

    Use the ``ok`` property for quick checks::

        result = await get_dialogs(client)
        if result.ok:
            for d in result.payload:
                ...
        else:
            print(result.error)
    """

    payload: T | None = None
    error: TgError | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


# ---------------------------------------------------------------------------
# Payload DTOs (T7) — only the fields the caller actually needs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DialogInfo:
    """Lightweight representation of a Telegram dialog (T7, T9).

    A "dialog" in the Telegram API represents any conversation the user
    participates in: a one-to-one user chat, a group, or a channel.
    """

    id: int
    name: str
    type: str  # "User" | "Chat" | "Channel"
    username: str | None = None
    unread_count: int = 0


@dataclass(frozen=True)
class MessageInfo:
    """Lightweight representation of a single message (T7)."""

    id: int
    dialog_id: int
    text: str
    date: datetime
    sender_id: int | None = None
    sender_name: str | None = None
    has_media: bool = False
    media_type: str | None = None  # e.g. "photo", "document", "video"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MediaResult:
    """Result of a media download (F6)."""

    message_id: int
    file_path: str
    mime_type: str | None = None
    size_bytes: int | None = None


@dataclass(frozen=True)
class SessionInfo:
    """Result of a session validation (F8)."""

    valid: bool
    user_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    phone: str | None = None


@dataclass(frozen=True)
class ServiceStatus:
    """Result of an availability check (F7)."""

    available: bool
    latency_ms: float | None = None
