"""
Unit tests for src/commands/init_cmd.py — interactive session setup.

Tests cover:
- F10-a: Existing config detection with user choice [A] or [B]
- F10-b: User interruption guidance message
- F10-c: Login code callback with graceful Ctrl+C handling
- F10-d: Consistent KeyboardInterrupt handling (no tracebacks)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

_cli_root = Path(__file__).resolve().parents[3]
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))


class TestInitExistingConfigDetection:
    """Tests for F10-a: Existing config detection and user choice."""

    def test_existing_config_choice_a_exit(self, tmp_path, monkeypatch, capsys):
        """F10-a: File exists, user chooses [A] (exit), should exit(0)."""
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text("telegram:\n  api_id: 123\n")

        # Change working directory to tmp_path
        monkeypatch.chdir(tmp_path)

        # Mock input to return empty string (defaults to [A])
        monkeypatch.setattr("builtins.input", lambda prompt: "")

        from src.commands.init_cmd import run_init
        with pytest.raises(SystemExit) as exc_info:
            run_init()

        assert exc_info.value.code == 0
        out = capsys.readouterr()
        assert "Found existing config.yaml" in out.out

    def test_existing_config_choice_a_explicit(self, tmp_path, monkeypatch, capsys):
        """F10-a: File exists, user explicitly chooses [A], should exit(0)."""
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text("telegram:\n  api_id: 123\n")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("builtins.input", lambda prompt: "A")

        from src.commands.init_cmd import run_init
        with pytest.raises(SystemExit) as exc_info:
            run_init()

        assert exc_info.value.code == 0

    def test_existing_config_choice_b_create_example(self, tmp_path, monkeypatch, capsys):
        """F10-a: File exists, user chooses [B], should create config.yaml.example and exit(0)."""
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text("telegram:\n  api_id: 123\n")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("builtins.input", lambda prompt: "B")

        from src.commands.init_cmd import run_init
        with pytest.raises(SystemExit) as exc_info:
            run_init()

        assert exc_info.value.code == 0
        out = capsys.readouterr()
        assert "Example config created" in out.out
        
        # Verify example file was created
        example_file = tmp_path / "config.yaml.example"
        assert example_file.exists()
        content = example_file.read_text()
        assert "YOUR_API_ID_HERE" in content
        assert "YOUR_API_HASH_HERE" in content

    def test_existing_config_choice_invalid_defaults_to_a(self, tmp_path, monkeypatch, capsys):
        """F10-a: File exists, user enters invalid choice, defaults to [A], should exit(0)."""
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text("telegram:\n  api_id: 123\n")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("builtins.input", lambda prompt: "INVALID")

        from src.commands.init_cmd import run_init
        with pytest.raises(SystemExit) as exc_info:
            run_init()

        assert exc_info.value.code == 0

    def test_existing_config_ctrl_c_interrupt(self, tmp_path, monkeypatch, capsys):
        """F10-d: User presses Ctrl+C during existing config menu, should exit(1) with message."""
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text("telegram:\n  api_id: 123\n")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("builtins.input", lambda prompt: (_ for _ in ()).throw(KeyboardInterrupt()))

        from src.commands.init_cmd import run_init
        with pytest.raises(SystemExit) as exc_info:
            run_init()

        assert exc_info.value.code == 1
        out = capsys.readouterr()
        assert "Setup cancelled by user" in out.out


class TestInterruptionGuidance:
    """Tests for F10-b: User interruption guidance message."""

    def test_no_existing_config_shows_guidance(self, tmp_path, monkeypatch, capsys):
        """F10-b: When no config exists, guidance message appears before prompts."""
        monkeypatch.chdir(tmp_path)
        
        def input_side_effect(prompt):
            # Raise after first prompt to stop execution
            if "api_id" in prompt:
                raise KeyboardInterrupt()
            return ""

        monkeypatch.setattr("builtins.input", input_side_effect)

        from src.commands.init_cmd import run_init
        with pytest.raises(SystemExit) as exc_info:
            run_init()

        assert exc_info.value.code == 1
        out = capsys.readouterr()
        assert "To interrupt at any time, press Ctrl+C" in out.out


class TestPromptCredentialsInterrupt:
    """Tests for F10-c & F10-d: Keyboard interrupt handling in credential prompts."""

    def test_interrupt_at_api_id(self, monkeypatch, capsys):
        """F10-d: KeyboardInterrupt during api_id prompt, graceful exit(1) no traceback."""
        monkeypatch.setattr("builtins.input", lambda prompt: (_ for _ in ()).throw(KeyboardInterrupt()))

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        out = capsys.readouterr()
        assert "Setup cancelled by user" in out.out

    def test_interrupt_at_api_hash(self, monkeypatch, capsys):
        """F10-d: KeyboardInterrupt during api_hash prompt, graceful exit(1)."""
        inputs = iter(["12345", None])  # Second call will raise
        
        def input_side_effect(prompt):
            val = next(inputs)
            if val is None:
                raise KeyboardInterrupt()
            return val

        monkeypatch.setattr("builtins.input", input_side_effect)

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        out = capsys.readouterr()
        assert "Setup cancelled by user" in out.out

    def test_interrupt_at_phone(self, monkeypatch, capsys):
        """F10-d: KeyboardInterrupt during phone prompt, graceful exit(1)."""
        inputs = iter(["12345", "hash", None])  # Third call will raise

        def input_side_effect(prompt):
            val = next(inputs)
            if val is None:
                raise KeyboardInterrupt()
            return val

        monkeypatch.setattr("builtins.input", input_side_effect)

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        out = capsys.readouterr()
        assert "Setup cancelled by user" in out.out

    def test_interrupt_eof(self, monkeypatch, capsys):
        """F10-d: EOFError (Ctrl+D) is handled gracefully like KeyboardInterrupt."""
        monkeypatch.setattr("builtins.input", lambda prompt: (_ for _ in ()).throw(EOFError()))

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        out = capsys.readouterr()
        assert "Setup cancelled by user" in out.out


class TestCredentialValidation:
    """Tests for validation and error handling in credential prompts."""

    def test_invalid_api_id_non_numeric(self, monkeypatch, capsys):
        """F10-d: Non-numeric api_id exits(1) with error message, no traceback."""
        monkeypatch.setattr("builtins.input", lambda prompt: "not_a_number")

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "api_id must be a number" in err

    def test_empty_api_hash(self, monkeypatch, capsys):
        """F10-d: Empty api_hash exits(1) with error message."""
        inputs = iter(["12345", ""])  # Hash is empty
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "api_hash cannot be empty" in err

    def test_empty_phone(self, monkeypatch, capsys):
        """F10-d: Empty phone exits(1) with error message."""
        inputs = iter(["12345", "hash", ""])  # Phone is empty
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "phone cannot be empty" in err

    def test_happy_path_valid_credentials(self, monkeypatch):
        """F10-d: Valid credentials accepted successfully."""
        inputs = iter(["12345", "abc_hash", "+49123456"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        from src.commands.init_cmd import _prompt_credentials
        result = _prompt_credentials()

        assert result["api_id"] == 12345
        assert result["api_hash"] == "abc_hash"
        assert result["phone"] == "+49123456"


class TestExampleConfigCreation:
    """Tests for F10-a option B: Creating example config."""

    def test_create_example_config_success(self, tmp_path):
        """F10-a: Creating example config.yaml.example succeeds."""
        from src.commands.init_cmd import _create_example_config

        config_yaml = tmp_path / "config.yaml"

        with pytest.raises(SystemExit) as exc_info:
            _create_example_config(config_yaml)

        assert exc_info.value.code == 0

        example_file = tmp_path / "config.yaml.example"
        assert example_file.exists()
        content = example_file.read_text()
        assert "api_id" in content
        assert "api_hash" in content
        assert "phone" in content
        assert "session" in content

    def test_create_example_config_permission_error(self, tmp_path, monkeypatch, capsys):
        """F10-d: OSError during example creation exits(1) with error message."""
        # Simulate permission error by making directory read-only
        config_yaml = tmp_path / "config.yaml"
        
        from src.commands.init_cmd import _create_example_config
        from pathlib import Path as PathClass
        
        # Mock write_text to raise OSError
        original_write = PathClass.write_text
        
        def mock_write_text(self, *args, **kwargs):
            if "config.yaml.example" in str(self):
                raise OSError("Permission denied")
            return original_write(self, *args, **kwargs)

        monkeypatch.setattr("pathlib.Path.write_text", mock_write_text)

        with pytest.raises(SystemExit) as exc_info:
            _create_example_config(config_yaml)

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "Cannot create example config" in err


class TestLoadExistingConfig:
    """Tests for loading existing config.yaml."""

    def test_load_existing_config_success(self, tmp_path):
        """Happy path: Load existing config with all required fields."""
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text(
            "telegram:\n"
            "  api_id: 99\n"
            "  api_hash: hash99\n"
            "  phone: '+491'\n"
            "  session: old_session_string\n"
        )

        from src.commands.init_cmd import _load_existing_config
        result = _load_existing_config(config_yaml)

        assert result["api_id"] == 99
        assert result["api_hash"] == "hash99"
        assert result["phone"] == "+491"
        assert result["session"] == "old_session_string"

    def test_load_existing_config_missing_field(self, tmp_path, capsys):
        """Missing field in config exits(1) with error message."""
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text(
            "telegram:\n"
            "  api_id: 99\n"
            "  api_hash: hash99\n"
        )  # Missing phone

        from src.commands.init_cmd import _load_existing_config
        with pytest.raises(SystemExit) as exc_info:
            _load_existing_config(config_yaml)

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "Missing" in err and "phone" in err

    def test_load_existing_config_invalid_yaml(self, tmp_path, capsys):
        """Invalid YAML exits(1) with error message."""
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text("invalid: yaml: content:")  # Invalid YAML

        from src.commands.init_cmd import _load_existing_config
        with pytest.raises(SystemExit) as exc_info:
            _load_existing_config(config_yaml)

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "Cannot read config.yaml" in err

    def test_load_existing_config_file_not_found(self, tmp_path, capsys):
        """Missing config file exits(1) with error message."""
        config_yaml = tmp_path / "nonexistent.yaml"

        from src.commands.init_cmd import _load_existing_config
        with pytest.raises(SystemExit) as exc_info:
            _load_existing_config(config_yaml)

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "Cannot read config.yaml" in err
