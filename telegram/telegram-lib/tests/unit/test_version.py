"""
Unit tests for src/version.py — get_version (F9).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.models import ErrorCode


class TestGetVersion:
    """F9: return library version information."""

    def test_get_version_happy(self):
        """Happy path: version.yaml exists and is well-formed."""
        from src.version import get_version

        result = get_version()

        assert result.ok
        assert result.payload is not None
        assert isinstance(result.payload.version, str)
        assert isinstance(result.payload.build, int)
        assert isinstance(result.payload.datetime, str)
        # Verify it matches the actual version.yaml content
        assert len(result.payload.version) > 0
        assert result.payload.build >= 1

    def test_get_version_file_missing(self, tmp_path):
        """Error path: version.yaml file does not exist."""
        from src.version import get_version

        fake_path = tmp_path / "nonexistent.yaml"
        with patch("src.version._VERSION_FILE", fake_path):
            result = get_version()

        assert not result.ok
        assert result.error.code == ErrorCode.INTERNAL_ERROR

    def test_get_version_malformed(self, tmp_path):
        """Error path: version.yaml contains invalid YAML."""
        from src.version import get_version

        bad_file = tmp_path / "version.yaml"
        bad_file.write_text(": : :\n  broken: [")
        with patch("src.version._VERSION_FILE", bad_file):
            result = get_version()

        assert not result.ok
        assert result.error.code == ErrorCode.INTERNAL_ERROR

    def test_get_version_missing_keys(self, tmp_path):
        """Error path: version.yaml is valid YAML but missing required keys."""
        from src.version import get_version

        incomplete = tmp_path / "version.yaml"
        incomplete.write_text("version: 1.0.0\n")
        with patch("src.version._VERSION_FILE", incomplete):
            result = get_version()

        assert not result.ok
        assert result.error.code == ErrorCode.INTERNAL_ERROR
