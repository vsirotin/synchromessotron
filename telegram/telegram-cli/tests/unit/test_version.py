"""
Unit tests for src/version.py — CLI version reader.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import sys

_cli_root = Path(__file__).resolve().parents[3]
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))

from src.version import get_cli_version, _VERSION_FILE


class TestGetCliVersion:
    """Tests for get_cli_version()."""

    def test_get_cli_version_happy(self):
        """Happy path: version.yaml is readable and well-formed."""
        result = get_cli_version()
        assert result["version"] == "1.0.3"
        assert result["build"] == 1
        assert "datetime" in result

    def test_get_cli_version_missing(self, tmp_path):
        """Missing version.yaml returns fallback dict."""
        fake_path = tmp_path / "nonexistent.yaml"
        with patch("src.version._VERSION_FILE", fake_path):
            result = get_cli_version()
        assert result["version"] == "unknown"
        assert result["build"] == 0

    def test_get_cli_version_malformed(self, tmp_path):
        """Malformed YAML still returns partial data (no crash)."""
        bad_file = tmp_path / "version.yaml"
        bad_file.write_text("not_a_key_value")
        with patch("src.version._VERSION_FILE", bad_file):
            result = get_cli_version()
        assert result["version"] == "unknown"
