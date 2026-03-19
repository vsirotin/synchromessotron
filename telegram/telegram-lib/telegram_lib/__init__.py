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
    get_version         — Return library version info (F9).

Models:
    TgResult, TgError, ErrorCode,
    DialogInfo, MessageInfo, MediaResult, SessionInfo, ServiceStatus,
    VersionInfo
"""

from telegram_lib.client import create_client
from telegram_lib.dialogs import get_dialogs
from telegram_lib.health import check_availability, validate_session
from telegram_lib.media import download_media
from telegram_lib.messages import delete_message, edit_message, read_messages, send_message
from telegram_lib.models import (
    DialogInfo,
    ErrorCode,
    MediaResult,
    MessageInfo,
    ServiceStatus,
    SessionInfo,
    TgError,
    TgResult,
    VersionInfo,
)
from telegram_lib.version import get_version

__all__ = [
    # factory
    "create_client",
    # functions (F1–F9)
    "get_dialogs",
    "read_messages",
    "send_message",
    "edit_message",
    "delete_message",
    "download_media",
    "check_availability",
    "validate_session",
    "get_version",
    # models
    "TgResult",
    "TgError",
    "ErrorCode",
    "DialogInfo",
    "MessageInfo",
    "MediaResult",
    "SessionInfo",
    "ServiceStatus",
    "VersionInfo",
]
