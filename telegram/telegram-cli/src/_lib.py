"""
Adapter for importing telegram-lib modules (avoids ``src`` namespace collision).

Both telegram-cli and telegram-lib use ``src`` as their package name.
This module imports telegram-lib functions via importlib to avoid conflicts.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_LIB_ROOT = Path(__file__).resolve().parents[2] / "telegram-lib"


def _load_lib_module(name: str) -> ModuleType:
    """Load a module from telegram-lib/src by file path."""
    module_path = _LIB_ROOT / "src" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"telegram_lib_{name}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load telegram-lib module: {module_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"telegram_lib_{name}"] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_lib_path() -> None:
    """Add telegram-lib root to sys.path if not already there (for transitive deps)."""
    lib_str = str(_LIB_ROOT)
    if lib_str not in sys.path:
        sys.path.insert(0, lib_str)


# Lazy-loaded references
_models_mod: ModuleType | None = None
_client_mod: ModuleType | None = None
_health_mod: ModuleType | None = None
_dialogs_mod: ModuleType | None = None
_messages_mod: ModuleType | None = None
_version_mod: ModuleType | None = None


def get_lib_models():
    """Return the telegram-lib models module."""
    global _models_mod
    if _models_mod is None:
        _ensure_lib_path()
        _models_mod = _load_lib_module("models")
    return _models_mod


def create_client(api_id: int, api_hash: str, session: str = ""):
    """Delegate to telegram-lib create_client."""
    global _client_mod
    if _client_mod is None:
        _ensure_lib_path()
        _client_mod = _load_lib_module("client")
    return _client_mod.create_client(api_id, api_hash, session)


async def check_availability(client):
    """Delegate to telegram-lib check_availability."""
    global _health_mod
    if _health_mod is None:
        _ensure_lib_path()
        _health_mod = _load_lib_module("health")
    return await _health_mod.check_availability(client)


async def validate_session(client):
    """Delegate to telegram-lib validate_session."""
    global _health_mod
    if _health_mod is None:
        _ensure_lib_path()
        _health_mod = _load_lib_module("health")
    return await _health_mod.validate_session(client)


async def get_dialogs(client, *, limit: int = 100):
    """Delegate to telegram-lib get_dialogs."""
    global _dialogs_mod
    if _dialogs_mod is None:
        _ensure_lib_path()
        _dialogs_mod = _load_lib_module("dialogs")
    return await _dialogs_mod.get_dialogs(client, limit=limit)


def get_lib_version():
    """Delegate to telegram-lib get_version."""
    global _version_mod
    if _version_mod is None:
        _ensure_lib_path()
        _version_mod = _load_lib_module("version")
    return _version_mod.get_version()


def _get_messages_mod():
    """Lazy-load the telegram-lib messages module."""
    global _messages_mod
    if _messages_mod is None:
        _ensure_lib_path()
        _messages_mod = _load_lib_module("messages")
    return _messages_mod


async def count_messages(client, dialog_id, *, since=None):
    """Delegate to telegram-lib count_messages."""
    return await _get_messages_mod().count_messages(client, dialog_id, since=since)


async def read_messages(client, dialog_id, *, since=None, limit=100):
    """Delegate to telegram-lib read_messages."""
    return await _get_messages_mod().read_messages(client, dialog_id, since=since, limit=limit)


async def send_message(client, dialog_id, text):
    """Delegate to telegram-lib send_message."""
    return await _get_messages_mod().send_message(client, dialog_id, text)


async def edit_message(client, dialog_id, message_id, new_text):
    """Delegate to telegram-lib edit_message."""
    return await _get_messages_mod().edit_message(client, dialog_id, message_id, new_text)


async def delete_message(client, dialog_id, message_ids):
    """Delegate to telegram-lib delete_message."""
    return await _get_messages_mod().delete_message(client, dialog_id, message_ids)


# ---------------------------------------------------------------------------
# Media module
# ---------------------------------------------------------------------------

_media_mod: ModuleType | None = None


def _get_media_mod():
    """Lazy-load the telegram-lib media module."""
    global _media_mod
    if _media_mod is None:
        _ensure_lib_path()
        _media_mod = _load_lib_module("media")
    return _media_mod


async def download_media(client, dialog_id, message_id, *, dest_dir="."):
    """Delegate to telegram-lib download_media."""
    return await _get_media_mod().download_media(
        client, dialog_id, message_id, dest_dir=dest_dir,
    )
