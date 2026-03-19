"""
Thin re-export layer for telegram-lib functions used by telegram-cli.
"""

from __future__ import annotations

from telegram_lib.client import create_client
from telegram_lib.dialogs import get_dialogs
from telegram_lib.health import check_availability, validate_session
from telegram_lib.media import download_media
from telegram_lib.messages import count_messages, delete_message, edit_message, read_messages, send_message
from telegram_lib.version import get_version as get_lib_version
import telegram_lib.models as _models_module


def get_lib_models():
    """Return the telegram-lib models module."""
    return _models_module
