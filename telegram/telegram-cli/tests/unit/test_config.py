"""
Unit tests for src/config.py — configuration loader.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_cli_root = Path(__file__).resolve().parents[3]
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))

from src.config import load_config, resolve_outdir, save_config


class TestLoadConfig:
    """Tests for load_config()."""

    def test_load_config_happy(self, tmp_path):
        """Happy path: valid config.yaml with all required fields."""
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            "telegram:\n"
            "  api_id: 12345\n"
            "  api_hash: abc123\n"
            "  phone: '+1234567890'\n"
            "  session: sess_string\n"
        )
        result = load_config(cfg)
        assert result["api_id"] == 12345
        assert result["api_hash"] == "abc123"
        assert result["phone"] == "+1234567890"
        assert result["session"] == "sess_string"

    def test_load_config_missing(self, tmp_path):
        """Missing config.yaml exits with code 1."""
        with pytest.raises(SystemExit) as exc_info:
            load_config(tmp_path / "nonexistent.yaml")
        assert exc_info.value.code == 1

    def test_load_config_no_tg(self, tmp_path):
        """Config without 'telegram' section exits with code 1."""
        cfg = tmp_path / "config.yaml"
        cfg.write_text("other_key: value\n")
        with pytest.raises(SystemExit) as exc_info:
            load_config(cfg)
        assert exc_info.value.code == 1

    def test_load_config_missing_field(self, tmp_path):
        """Config missing a required field exits with code 1."""
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            "telegram:\n"
            "  api_id: 12345\n"
            "  api_hash: abc123\n"
        )
        with pytest.raises(SystemExit) as exc_info:
            load_config(cfg)
        assert exc_info.value.code == 1

    def test_load_config_invalid_yaml(self, tmp_path):
        """Invalid YAML syntax exits with code 1."""
        cfg = tmp_path / "config.yaml"
        cfg.write_text("telegram:\n  api_id: [unclosed\n")
        with pytest.raises(SystemExit) as exc_info:
            load_config(cfg)
        assert exc_info.value.code == 1

    def test_load_config_optional_fields(self, tmp_path):
        """Optional fields output_dir and split_threshold are read."""
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            "telegram:\n"
            "  api_id: 12345\n"
            "  api_hash: abc123\n"
            "  phone: '+1234567890'\n"
            "  session: sess\n"
            "  output_dir: /tmp/out\n"
            "  split_threshold: 100\n"
        )
        result = load_config(cfg)
        assert result["output_dir"] == "/tmp/out"
        assert result["split_threshold"] == 100


class TestSaveConfig:
    """Tests for save_config()."""

    def test_save_config_happy(self, tmp_path):
        """Save and reload config round-trips correctly."""
        cfg_path = tmp_path / "config.yaml"
        config = {"api_id": 12345, "api_hash": "abc", "phone": "+1", "session": "s"}
        save_config(config, cfg_path)
        loaded = load_config(cfg_path)
        assert loaded["api_id"] == 12345
        assert loaded["session"] == "s"

    def test_save_config_no_write(self, tmp_path):
        """Unwritable path exits with code 1."""
        cfg_path = tmp_path / "readonly" / "subdir" / "config.yaml"
        # Create the parent as a file to make mkdir fail
        (tmp_path / "readonly").write_text("block")
        config = {"api_id": 1, "api_hash": "a", "phone": "+1", "session": "s"}
        with pytest.raises(SystemExit) as exc_info:
            save_config(config, cfg_path)
        assert exc_info.value.code == 1


class TestResolveOutdir:
    """Tests for resolve_outdir()."""

    def test_resolve_outdir_none(self):
        """Neither CLI nor config sets outdir → None."""
        assert resolve_outdir(None, {}) is None

    def test_resolve_outdir_cli_only(self, tmp_path):
        """Only --outdir from CLI."""
        result = resolve_outdir(str(tmp_path / "out"), {})
        assert result == (tmp_path / "out").resolve()

    def test_resolve_outdir_cfg_only(self, tmp_path):
        """Only output_dir from config."""
        result = resolve_outdir(None, {"output_dir": str(tmp_path / "data")})
        assert result == (tmp_path / "data").resolve()

    def test_resolve_outdir_match(self, tmp_path):
        """Both set to the same path → accepted."""
        path = str(tmp_path / "same")
        result = resolve_outdir(path, {"output_dir": path})
        assert result == (tmp_path / "same").resolve()

    def test_resolve_outdir_conflict(self, tmp_path):
        """Different paths → exit code 1."""
        with pytest.raises(SystemExit) as exc_info:
            resolve_outdir(str(tmp_path / "a"), {"output_dir": str(tmp_path / "b")})
        assert exc_info.value.code == 1
