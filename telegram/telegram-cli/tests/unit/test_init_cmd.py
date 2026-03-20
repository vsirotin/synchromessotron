"""
Unit tests for src/commands/init_cmd.py — interactive session setup.

Tests cover the decision tree flow:
1. Show interruption guidance
2. Search for existing config
3. Ask if config exists elsewhere  
4. Ask if user has credentials noted
5. Offer example file creation
6. Prompt for credentials and authenticate

All tests follow the decision tree and include graceful error handling.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

_cli_root = Path(__file__).resolve().parents[3]
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))


class TestInformConfigFound:
    """Tests for _inform_config_found() function."""

    def test_informs_and_exits(self, tmp_path, capsys):
        """Config found → inform user and exit(0)."""
        config_yaml = tmp_path / "config.yaml"

        from src.commands.init_cmd import _inform_config_found
        with pytest.raises(SystemExit) as exc_info:
            _inform_config_found(config_yaml)

        assert exc_info.value.code == 0
        out = capsys.readouterr()
        assert "Found config.yaml" in out.out
        assert "whoami" in out.out


class TestAskHasConfigElsewhere:
    """Tests for _ask_has_config_elsewhere() function."""

    def test_user_says_yes(self, monkeypatch, capsys):
        """User answers yes → exit(0) with recommendation."""
        monkeypatch.setattr("builtins.input", lambda prompt: "y")

        from src.commands.init_cmd import _ask_has_config_elsewhere
        with pytest.raises(SystemExit) as exc_info:
            _ask_has_config_elsewhere()

        assert exc_info.value.code == 0
        out = capsys.readouterr()
        assert "copy" in out.out.lower()

    def test_user_says_no(self, monkeypatch):
        """User answers no → return False."""
        monkeypatch.setattr("builtins.input", lambda prompt: "n")

        from src.commands.init_cmd import _ask_has_config_elsewhere
        result = _ask_has_config_elsewhere()
        assert result is False

    def test_user_interrupts(self, monkeypatch, capsys):
        """User presses Ctrl+C → exit(1) gracefully."""
        monkeypatch.setattr("builtins.input", lambda prompt: (_ for _ in ()).throw(KeyboardInterrupt()))

        from src.commands.init_cmd import _ask_has_config_elsewhere
        with pytest.raises(SystemExit) as exc_info:
            _ask_has_config_elsewhere()

        assert exc_info.value.code == 1
        out = capsys.readouterr()
        assert "Setup cancelled" in out.out


class TestAskHasCredentialsNoted:
    """Tests for _ask_has_credentials_noted() function."""

    def test_user_says_yes(self, monkeypatch):
        """User answers yes → return True."""
        monkeypatch.setattr("builtins.input", lambda prompt: "yes")

        from src.commands.init_cmd import _ask_has_credentials_noted
        result = _ask_has_credentials_noted()
        assert result is True

    def test_user_says_no(self, monkeypatch):
        """User answers no → return False."""
        monkeypatch.setattr("builtins.input", lambda prompt: "n")

        from src.commands.init_cmd import _ask_has_credentials_noted
        result = _ask_has_credentials_noted()
        assert result is False

    def test_user_interrupts(self, monkeypatch, capsys):
        """User presses Ctrl+C → exit(1)."""
        monkeypatch.setattr("builtins.input", lambda prompt: (_ for _ in ()).throw(KeyboardInterrupt()))

        from src.commands.init_cmd import _ask_has_credentials_noted
        with pytest.raises(SystemExit) as exc_info:
            _ask_has_credentials_noted()

        assert exc_info.value.code == 1


class TestAskCreateExampleFile:
    """Tests for _ask_create_example_file() function."""

    def test_user_says_yes(self, monkeypatch):
        """User answers yes → return True."""
        monkeypatch.setattr("builtins.input", lambda prompt: "y")

        from src.commands.init_cmd import _ask_create_example_file
        result = _ask_create_example_file()
        assert result is True

    def test_user_says_no(self, monkeypatch):
        """User answers no → return False."""
        monkeypatch.setattr("builtins.input", lambda prompt: "no")

        from src.commands.init_cmd import _ask_create_example_file
        result = _ask_create_example_file()
        assert result is False

    def test_user_interrupts(self, monkeypatch, capsys):
        """User presses Ctrl+C → exit(1)."""
        monkeypatch.setattr("builtins.input", lambda prompt: (_ for _ in ()).throw(KeyboardInterrupt()))

        from src.commands.init_cmd import _ask_create_example_file
        with pytest.raises(SystemExit) as exc_info:
            _ask_create_example_file()

        assert exc_info.value.code == 1


class TestCreateExampleConfig:
    """Tests for _create_example_config() function."""

    def test_successfully_creates_example(self, tmp_path, capsys):
        """Example file created successfully → exit(0)."""
        config_yaml = tmp_path / "config.yaml"

        from src.commands.init_cmd import _create_example_config
        with pytest.raises(SystemExit) as exc_info:
            _create_example_config(config_yaml)

        assert exc_info.value.code == 0
        example_file = tmp_path / "config.yaml.example"
        assert example_file.exists()
        content = example_file.read_text()
        assert "YOUR_API_ID_HERE" in content
        assert "YOUR_API_HASH_HERE" in content
        out = capsys.readouterr()
        assert "Example config created" in out.out

    def test_permission_error(self, tmp_path, monkeypatch, capsys):
        """OSError during creation → exit(2) with error message."""
        config_yaml = tmp_path / "config.yaml"

        from src.commands.init_cmd import _create_example_config
        from pathlib import Path as PathClass

        original_write = PathClass.write_text

        def mock_write_text(self, *args, **kwargs):
            if "config.yaml.example" in str(self):
                raise OSError("Permission denied")
            return original_write(self, *args, **kwargs)

        monkeypatch.setattr("pathlib.Path.write_text", mock_write_text)

        with pytest.raises(SystemExit) as exc_info:
            _create_example_config(config_yaml)

        assert exc_info.value.code == 2
        err = capsys.readouterr().err
        assert "Cannot create" in err


class TestPromptCredentials:
    """Tests for _prompt_credentials() function."""

    def test_valid_credentials(self, monkeypatch):
        """Valid inputs → return dict."""
        inputs = iter(["12345", "hash_abc", "+1234567890"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        from src.commands.init_cmd import _prompt_credentials
        result = _prompt_credentials()

        assert result["api_id"] == 12345
        assert result["api_hash"] == "hash_abc"
        assert result["phone"] == "+1234567890"

    def test_invalid_api_id(self, monkeypatch, capsys):
        """Non-numeric api_id → exit(1)."""
        monkeypatch.setattr("builtins.input", lambda prompt: "not_a_number")

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "api_id must be a number" in err

    def test_empty_api_hash(self, monkeypatch, capsys):
        """Empty api_hash → exit(1)."""
        inputs = iter(["12345", ""])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "api_hash" in err and "empty" in err

    def test_empty_phone(self, monkeypatch, capsys):
        """Empty phone → exit(1)."""
        inputs = iter(["12345", "hash", ""])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "phone" in err

    def test_keyboard_interrupt(self, monkeypatch, capsys):
        """Ctrl+C → exit(1) gracefully."""
        monkeypatch.setattr("builtins.input", lambda prompt: (_ for _ in ()).throw(KeyboardInterrupt()))

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        out = capsys.readouterr()
        assert "Setup cancelled" in out.out

    def test_eof_error(self, monkeypatch, capsys):
        """EOFError (Ctrl+D) → exit(1) gracefully."""
        monkeypatch.setattr("builtins.input", lambda prompt: (_ for _ in ()).throw(EOFError()))

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        out = capsys.readouterr()
        assert "Setup cancelled" in out.out


class TestDecisionTreeIntegration:
    """Integration tests for the full decision tree flow."""

    def test_config_found_exits_early(self, tmp_path, monkeypatch, capsys):
        """Config exists → exit(0) immediately."""
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text("telegram:\n  api_id: 123\n")
        
        monkeypatch.chdir(tmp_path)

        from src.commands.init_cmd import run_init
        with pytest.raises(SystemExit) as exc_info:
            run_init()

        assert exc_info.value.code == 0
        out = capsys.readouterr()
        assert "Found config.yaml" in out.out
        assert "To interrupt at any time" in out.out

    def test_has_config_elsewhere_exits(self, tmp_path, monkeypatch, capsys):
        """User has config elsewhere → exit(0)."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("builtins.input", lambda prompt: "y")

        from src.commands.init_cmd import run_init
        with pytest.raises(SystemExit) as exc_info:
            run_init()

        assert exc_info.value.code == 0
        out = capsys.readouterr()
        assert "copy config.yaml" in out.out.lower()

    def test_create_example_file_flow(self, tmp_path, monkeypatch, capsys):
        """User chooses to create example → exit(0) with example file."""
        monkeypatch.chdir(tmp_path)
        
        inputs = iter(["n", "y", "y"])  # no elsewhere, yes credentials, yes example
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        from src.commands.init_cmd import run_init
        with pytest.raises(SystemExit) as exc_info:
            run_init()

        assert exc_info.value.code == 0
        assert (tmp_path / "config.yaml.example").exists()
        out = capsys.readouterr()
        assert "Example config created" in out.out
