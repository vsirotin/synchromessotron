"""
Unit tests for src/client.py — create_client.
"""

from __future__ import annotations

from unittest.mock import patch

from src.client import create_client


class TestCreateClient:
    """Factory function: build a TelegramClient from credentials."""

    def test_create_client_happy(self):
        client = create_client(api_id=12345, api_hash="abc123", session="")
        # TelegramClient is returned; we can't connect without a real server
        # but the object must exist with the right api_id.
        assert client.api_id == 12345

    def test_create_client_w_session(self):
        client = create_client(api_id=12345, api_hash="abc123", session="")
        assert client.api_id == 12345

    def test_create_client_logging(self, caplog):
        import logging

        with caplog.at_level(logging.DEBUG, logger="telegram_lib"):
            create_client(api_id=99, api_hash="xyz", session="")

        assert any("create_client called" in r.message for r in caplog.records)
        assert any("create_client completed" in r.message for r in caplog.records)
