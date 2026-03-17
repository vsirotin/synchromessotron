"""
Unit tests for src/errors.py — error formatting.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_cli_root = Path(__file__).resolve().parents[3]
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))

# Import telegram-lib models
_lib_root = Path(__file__).resolve().parents[3] / ".." / "telegram-lib"
if str(_lib_root.resolve()) not in sys.path:
    sys.path.insert(0, str(_lib_root.resolve()))

from src.errors import format_error_and_exit


class _FakeErrorCode:
    """Minimal stand-in for ErrorCode enum."""
    def __init__(self, value: str):
        self.value = value


class _FakeError:
    """Minimal stand-in for TgError."""
    def __init__(self, code_str: str, message: str, retry_after=None):
        self.code = _FakeErrorCode(code_str)
        self.message = message
        self.retry_after = retry_after


class TestFormatErrorAndExit:
    """Tests for format_error_and_exit()."""

    def test_format_error_basic(self, capsys):
        """Basic error prints code and message to stderr, exits 2."""
        err = _FakeError("NETWORK_ERROR", "Cannot connect")
        with pytest.raises(SystemExit) as exc_info:
            format_error_and_exit(err)
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "Error [NETWORK_ERROR]" in captured.err
        assert "Cannot connect" in captured.err

    def test_format_error_rate(self, capsys):
        """RATE_LIMITED error includes retry_after line."""
        err = _FakeError("RATE_LIMITED", "Too many requests", retry_after=30.0)
        with pytest.raises(SystemExit) as exc_info:
            format_error_and_exit(err)
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "retry_after: 30" in captured.err

    def test_format_error_no_retry(self, capsys):
        """Non-rate-limited error does not print retry_after."""
        err = _FakeError("AUTH_FAILED", "Banned")
        with pytest.raises(SystemExit):
            format_error_and_exit(err)
        captured = capsys.readouterr()
        assert "retry_after" not in captured.err
