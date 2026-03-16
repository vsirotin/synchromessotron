"""
telegram-lib — stateless Python wrapper functions for the Telegram API.

Public API:
    create_client       — Build a TelegramClient from credentials.
    get_dialogs         — List user's dialogs (F5).
    read_messages       — Read messages, full or incremental (F1).
    send_message        — Send a message (F2).
    edit_message        — Edit own message (F3).
    delete_message      — Delete own messages (F4).
    download_media      — Download media from a message (F6).
    check_availability  — Ping Telegram (F7).
    validate_session    — Validate a session string (F8).

Models:
    TgResult, TgError, ErrorCode,
    DialogInfo, MessageInfo, MediaResult, SessionInfo, ServiceStatus
"""

from src.client import create_client
from src.dialogs import get_dialogs
from src.health import check_availability, validate_session
from src.media import download_media
from src.messages import delete_message, edit_message, read_messages, send_message
from src.models import (
    DialogInfo,
    ErrorCode,
    MediaResult,
    MessageInfo,
    ServiceStatus,
    SessionInfo,
    TgError,
    TgResult,
)

__all__ = [
    # factory
    "create_client",
    # functions (F1–F8)
    "get_dialogs",
    "read_messages",
    "send_message",
    "edit_message",
    "delete_message",
    "download_media",
    "check_availability",
    "validate_session",
    # models
    "TgResult",
    "TgError",
    "ErrorCode",
    "DialogInfo",
    "MessageInfo",
    "MediaResult",
    "SessionInfo",
    "ServiceStatus",
]
