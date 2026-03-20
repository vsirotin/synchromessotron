"""
Unit tests for commands: whoami, ping, get_dialogs, init, version, send, edit, delete.

All tests mock telegram-lib calls to avoid network access.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
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


class _FakeMessageInfo:
    def __init__(self, id, date, text):
        self.id = id
        self.date = date
        self.text = text


class _FakeMediaResult:
    def __init__(self, message_id, file_path, mime_type=None, size_bytes=None):
        self.message_id = message_id
        self.file_path = file_path
        self.mime_type = mime_type
        self.size_bytes = size_bytes


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


# ---------------------------------------------------------------------------
# Send tests
# ---------------------------------------------------------------------------


class TestSend:

    def test_send_happy(self, capsys):
        """Happy path: prints JSON with id, date, text."""
        dt = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        msg = _FakeMessageInfo(id=42, date=dt, text="Hello!")
        result = _FakeResult(payload=msg)

        with (
            patch("src.commands.send.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.send.create_client") as mock_cc,
            patch("src.commands.send.send_message", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.send import run_send
            run_send(dialog_id=100, text="Hello!")

        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["id"] == 42
        assert data["text"] == "Hello!"
        assert "2026-06-01" in data["date"]

    def test_send_error(self, capsys):
        """Error exits with code 2."""
        err = _FakeError("NOT_FOUND", "Dialog not found")
        result = _FakeResult(error=err)

        with (
            patch("src.commands.send.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.send.create_client") as mock_cc,
            patch("src.commands.send.send_message", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.send import run_send
            with pytest.raises(SystemExit) as exc_info:
                run_send(dialog_id=999, text="test")
            assert exc_info.value.code == 2

        captured = capsys.readouterr()
        assert "NOT_FOUND" in captured.err


# ---------------------------------------------------------------------------
# Edit tests
# ---------------------------------------------------------------------------


class TestEdit:

    def test_edit_happy(self, capsys):
        """Happy path: prints updated message JSON."""
        dt = datetime(2026, 6, 1, 13, 0, 0, tzinfo=timezone.utc)
        msg = _FakeMessageInfo(id=55, date=dt, text="Updated!")
        result = _FakeResult(payload=msg)

        with (
            patch("src.commands.edit.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.edit.create_client") as mock_cc,
            patch("src.commands.edit.edit_message", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.edit import run_edit
            run_edit(dialog_id=100, message_id=55, text="Updated!")

        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["id"] == 55
        assert data["text"] == "Updated!"

    def test_edit_error(self, capsys):
        """Error exits with code 2."""
        err = _FakeError("PERMISSION_DENIED", "Not your message")
        result = _FakeResult(error=err)

        with (
            patch("src.commands.edit.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.edit.create_client") as mock_cc,
            patch("src.commands.edit.edit_message", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.edit import run_edit
            with pytest.raises(SystemExit) as exc_info:
                run_edit(dialog_id=100, message_id=55, text="x")
            assert exc_info.value.code == 2

        captured = capsys.readouterr()
        assert "PERMISSION_DENIED" in captured.err


# ---------------------------------------------------------------------------
# Delete tests
# ---------------------------------------------------------------------------


class TestDelete:

    def test_delete_happy(self, capsys):
        """Happy path: prints list of deleted IDs."""
        result = _FakeResult(payload=[10, 11, 12])

        with (
            patch("src.commands.delete.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.delete.create_client") as mock_cc,
            patch("src.commands.delete.delete_message", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.delete import run_delete
            run_delete(dialog_id=100, message_ids=[10, 11, 12])

        out = capsys.readouterr().out
        data = json.loads(out)
        assert data == [10, 11, 12]

    def test_delete_error(self, capsys):
        """Error exits with code 2."""
        err = _FakeError("NOT_FOUND", "Messages not found")
        result = _FakeResult(error=err)

        with (
            patch("src.commands.delete.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.delete.create_client") as mock_cc,
            patch("src.commands.delete.delete_message", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.delete import run_delete
            with pytest.raises(SystemExit) as exc_info:
                run_delete(dialog_id=100, message_ids=[999])
            assert exc_info.value.code == 2

        captured = capsys.readouterr()
        assert "NOT_FOUND" in captured.err


# ---------------------------------------------------------------------------
# Download-media tests
# ---------------------------------------------------------------------------


class TestDownloadMedia:

    def test_download_media_happy(self, capsys):
        """Happy path: prints JSON with file_path, mime_type, size_bytes."""
        media = _FakeMediaResult(
            message_id=42,
            file_path="/tmp/photo.jpg",
            mime_type="image/jpeg",
            size_bytes=12345,
        )
        result = _FakeResult(payload=media)

        with (
            patch("src.commands.download_media.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.download_media.create_client") as mock_cc,
            patch("src.commands.download_media.download_media", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.download_media import run_download_media
            run_download_media(dialog_id=100, message_id=42, dest="/tmp")

        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["message_id"] == 42
        assert data["file_path"] == "/tmp/photo.jpg"
        assert data["mime_type"] == "image/jpeg"
        assert data["size_bytes"] == 12345

    def test_download_media_error(self, capsys):
        """Error exits with code 2."""
        err = _FakeError("ENTITY_NOT_FOUND", "No media")
        result = _FakeResult(error=err)

        with (
            patch("src.commands.download_media.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.download_media.create_client") as mock_cc,
            patch("src.commands.download_media.download_media", new_callable=AsyncMock, return_value=result),
        ):
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cc.return_value = mock_client

            from src.commands.download_media import run_download_media
            with pytest.raises(SystemExit) as exc_info:
                run_download_media(dialog_id=100, message_id=999)
            assert exc_info.value.code == 2

        captured = capsys.readouterr()
        assert "ENTITY_NOT_FOUND" in captured.err


# ---------------------------------------------------------------------------
# Help tests
# ---------------------------------------------------------------------------


class TestHelp:

    def test_help_general(self, capsys):
        """General help prints command list."""
        from src.commands.help_cmd import run_help
        run_help(lang="en", command=None)

        out = capsys.readouterr().out
        assert "telegram-cli" in out
        assert "backup" in out
        assert "send" in out
        assert "Available commands:" in out

    def test_help_specific_command(self, capsys):
        """Command-specific help prints usage and description."""
        from src.commands.help_cmd import run_help
        run_help(lang="en", command="backup")

        out = capsys.readouterr().out
        assert "backup" in out
        assert "--since" in out
        assert "--estimate" in out

    def test_help_unknown_command(self, capsys):
        """Unknown command exits 1."""
        from src.commands.help_cmd import run_help
        with pytest.raises(SystemExit) as exc_info:
            run_help(lang="en", command="nonexistent")
        assert exc_info.value.code == 1

    def test_help_unsupported_lang(self, capsys):
        """Unsupported language falls back to English."""
        from src.commands.help_cmd import run_help
        run_help(lang="xx", command=None)

        out = capsys.readouterr().out
        err = capsys.readouterr().err if hasattr(capsys, 'readouterr') else ""
        # Should still print English help
        assert "telegram-cli" in out

    def test_help_empty_lang_fallback(self, capsys):
        """Empty placeholder language (ru) falls back to English."""
        from src.commands.help_cmd import run_help
        run_help(lang="ru", command=None)

        out = capsys.readouterr().out
        # Should show English help since ru.json is empty
        assert "telegram-cli" in out
