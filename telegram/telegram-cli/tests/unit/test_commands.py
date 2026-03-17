"""
Unit tests for commands: whoami, ping, get_dialogs, init, version.

All tests mock telegram-lib calls to avoid network access.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

_cli_root = Path(__file__).resolve().parents[3]
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))


# ---------------------------------------------------------------------------
# Fake telegram-lib types for testing
# ---------------------------------------------------------------------------


class _FakeErrorCode:
    def __init__(self, v):
        self.value = v


class _FakeError:
    def __init__(self, code_str, message, retry_after=None):
        self.code = _FakeErrorCode(code_str)
        self.message = message
        self.retry_after = retry_after


class _FakeResult:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error

    @property
    def ok(self):
        return self.error is None


class _FakeSessionInfo:
    def __init__(self, user_id, first_name, last_name, username, phone):
        self.valid = True
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.phone = phone


class _FakeServiceStatus:
    def __init__(self, available, latency_ms):
        self.available = available
        self.latency_ms = latency_ms


class _FakeDialogInfo:
    def __init__(self, id, name, type, username=None, unread_count=0):
        self.id = id
        self.name = name
        self.type = type
        self.username = username
        self.unread_count = unread_count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_config(tmp_path):
    """Write a valid config.yaml and return its path."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "telegram:\n"
        "  api_id: 12345\n"
        "  api_hash: abc123\n"
        "  phone: '+1234567890'\n"
        "  session: test_session\n"
    )
    return cfg


# ---------------------------------------------------------------------------
# Whoami tests
# ---------------------------------------------------------------------------


class TestWhoami:

    def test_whoami_happy(self, tmp_path, capsys):
        """Happy path: valid session prints user info."""
        cfg = _write_config(tmp_path)
        info = _FakeSessionInfo(123, "John", "Doe", "johndoe", "1234567890")
        result = _FakeResult(payload=info)

        with (
            patch("src.commands.whoami.load_config", return_value={
                "api_id": 12345, "api_hash": "abc", "session": "s"
            }),
            patch("src.commands.whoami.create_client") as mock_cc,
            patch("src.commands.whoami.validate_session", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.whoami import run_whoami
            run_whoami()

        out = capsys.readouterr().out
        assert "Session valid" in out
        assert "123" in out
        assert "John" in out

    def test_whoami_error(self, capsys):
        """Error from validate_session exits with code 2."""
        err = _FakeError("SESSION_INVALID", "Bad session")
        result = _FakeResult(error=err)

        with (
            patch("src.commands.whoami.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.whoami.create_client") as mock_cc,
            patch("src.commands.whoami.validate_session", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.whoami import run_whoami
            with pytest.raises(SystemExit) as exc_info:
                run_whoami()
            assert exc_info.value.code == 2

        captured = capsys.readouterr()
        assert "SESSION_INVALID" in captured.err


# ---------------------------------------------------------------------------
# Ping tests
# ---------------------------------------------------------------------------


class TestPing:

    def test_ping_happy(self, capsys):
        """Happy path: reachable Telegram prints latency."""
        status = _FakeServiceStatus(True, 42.3)
        result = _FakeResult(payload=status)

        with (
            patch("src.commands.ping.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.ping.create_client") as mock_cc,
            patch("src.commands.ping.check_availability", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.ping import run_ping
            run_ping()

        out = capsys.readouterr().out
        assert "42.3" in out
        assert "reachable" in out

    def test_ping_error(self, capsys):
        """Network error exits 2."""
        err = _FakeError("NETWORK_ERROR", "Connection refused")
        result = _FakeResult(error=err)

        with (
            patch("src.commands.ping.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.ping.create_client") as mock_cc,
            patch("src.commands.ping.check_availability", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.ping import run_ping
            with pytest.raises(SystemExit) as exc_info:
                run_ping()
            assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# Get-dialogs tests
# ---------------------------------------------------------------------------


class TestGetDialogs:

    def test_get_dialogs_happy(self, capsys):
        """Happy path: prints table of dialogs."""
        dialogs = [
            _FakeDialogInfo(123, "Alice", "User", "alice"),
            _FakeDialogInfo(-100, "Group Chat", "Chat"),
        ]
        result = _FakeResult(payload=dialogs)

        with (
            patch("src.commands.get_dialogs.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.get_dialogs.resolve_outdir", return_value=None),
            patch("src.commands.get_dialogs.create_client") as mock_cc,
            patch("src.commands.get_dialogs.get_dialogs", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.get_dialogs import run_get_dialogs
            run_get_dialogs(limit=None, outdir=None)

        out = capsys.readouterr().out
        assert "Alice" in out
        assert "Group Chat" in out
        assert "2 dialogs found" in out

    def test_get_dialogs_outdir(self, tmp_path, capsys):
        """With --outdir, dialogs.json is saved."""
        dialogs = [
            _FakeDialogInfo(1, "Test", "User", "test", 5),
        ]
        result = _FakeResult(payload=dialogs)
        outdir = tmp_path / "output"

        with (
            patch("src.commands.get_dialogs.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.get_dialogs.resolve_outdir", return_value=outdir),
            patch("src.commands.get_dialogs.create_client") as mock_cc,
            patch("src.commands.get_dialogs.get_dialogs", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.get_dialogs import run_get_dialogs
            run_get_dialogs(limit=None, outdir=str(outdir))

        json_file = outdir / "dialogs.json"
        assert json_file.exists()
        data = json.loads(json_file.read_text())
        assert len(data) == 1
        assert data[0]["name"] == "Test"
        assert data[0]["unread_count"] == 5

    def test_get_dialogs_error(self, capsys):
        """API error exits 2."""
        err = _FakeError("SESSION_INVALID", "Expired")
        result = _FakeResult(error=err)

        with (
            patch("src.commands.get_dialogs.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.get_dialogs.resolve_outdir", return_value=None),
            patch("src.commands.get_dialogs.create_client") as mock_cc,
            patch("src.commands.get_dialogs.get_dialogs", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.get_dialogs import run_get_dialogs
            with pytest.raises(SystemExit) as exc_info:
                run_get_dialogs(limit=None, outdir=None)
            assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# Version tests
# ---------------------------------------------------------------------------


class TestVersion:

    def test_version_happy(self, capsys):
        """Version command outputs JSON with cli and lib sections."""
        with (
            patch("src.commands.version_cmd.get_cli_version", return_value={
                "version": "0.5.0", "build": 1, "datetime": "2026-03-20T00:00:00Z"
            }),
            patch("src.commands.version_cmd.get_lib_version") as mock_lv,
        ):
            fake_payload = MagicMock()
            fake_payload.version = "1.2.0"
            fake_payload.build = 3
            fake_payload.datetime = "2026-03-18T00:00:00Z"
            mock_lv.return_value = _FakeResult(payload=fake_payload)

            from src.commands.version_cmd import run_version
            run_version()

        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["cli"]["version"] == "0.5.0"
        assert data["lib"]["version"] == "1.2.0"


# ---------------------------------------------------------------------------
# Init tests
# ---------------------------------------------------------------------------


class TestInit:

    def test_init_prompt_creds(self, monkeypatch, capsys):
        """When no config.yaml exists, prompts for credentials."""
        from src.commands.init_cmd import _prompt_credentials

        inputs = iter(["12345", "abc_hash", "+49123456"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        result = _prompt_credentials()
        assert result["api_id"] == 12345
        assert result["api_hash"] == "abc_hash"
        assert result["phone"] == "+49123456"

    def test_init_prompt_bad_id(self, monkeypatch):
        """Non-numeric api_id exits with code 1."""
        inputs = iter(["not_a_number"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

        from src.commands.init_cmd import _prompt_credentials
        with pytest.raises(SystemExit) as exc_info:
            _prompt_credentials()
        assert exc_info.value.code == 1

    def test_init_load_existing(self, tmp_path):
        """Existing config.yaml is loaded and reused."""
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            "telegram:\n"
            "  api_id: 99\n"
            "  api_hash: hash99\n"
            "  phone: '+491'\n"
            "  session: old\n"
        )
        from src.commands.init_cmd import _load_existing_config
        result = _load_existing_config(cfg)
        assert result["api_id"] == 99
        assert result["api_hash"] == "hash99"
