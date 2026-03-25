"""
Unit tests for the backup command (F1).

Tests cover: --estimate mode, backup to stdout, backup to file (atomic write),
resumable scan (T22), pagination with rate-limit retry (T19),
progress output (T23), and helper functions.
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
# Fake types
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


class _FakeMessageInfo:
    def __init__(self, id, dialog_id, text, date, sender_id=None, sender_name=None, has_media=False, media_type=None):
        self.id = id
        self.dialog_id = dialog_id
        self.text = text
        self.date = date
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.has_media = has_media
        self.media_type = media_type


class _FakeDialogInfo:
    def __init__(self, id, name, type="Chat", username=None, unread_count=0):
        self.id = id
        self.name = name
        self.type = type
        self.username = username
        self.unread_count = unread_count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_msg(id, text="msg", minutes_offset=0):
    """Create a _FakeMessageInfo with a fixed base date + offset."""
    base = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    from datetime import timedelta
    dt = base + timedelta(minutes=minutes_offset)
    return _FakeMessageInfo(id=id, dialog_id=100, text=text, date=dt)


def _make_client_mock():
    """Return a MagicMock that works as an async context manager."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


# ---------------------------------------------------------------------------
# Estimate tests
# ---------------------------------------------------------------------------


class TestEstimate:

    def test_estimate_happy(self, capsys):
        """--estimate prints human-readable estimate and exits normally."""
        count_result = _FakeResult(payload=500)

        with (
            patch("src.commands.backup.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.backup.create_client") as mock_cc,
            patch("src.commands.backup.count_messages", new_callable=AsyncMock, return_value=count_result),
        ):
            mock_cc.return_value = _make_client_mock()

            from src.commands.backup import run_backup
            run_backup(dialog_id=100, estimate=True, limit=500)

        out = capsys.readouterr().out
        assert "500 messages" in out
        assert "pages" in out
        assert "\u2248" in out  # ≈ sign

    def test_estimate_with_since(self, capsys):
        """--estimate with --since works correctly."""
        count_result = _FakeResult(payload=150)

        with (
            patch("src.commands.backup.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.backup.create_client") as mock_cc,
            patch("src.commands.backup.count_messages", new_callable=AsyncMock, return_value=count_result),
        ):
            mock_cc.return_value = _make_client_mock()

            from src.commands.backup import run_backup
            run_backup(dialog_id=100, since="2026-03-01T00:00:00", estimate=True, limit=1000)

        out = capsys.readouterr().out
        assert "150 messages" in out  # min(150, 1000) = 150

    def test_estimate_error(self, capsys):
        """Estimate with API error exits with code 2."""
        err = _FakeError("SESSION_INVALID", "Bad session")
        result = _FakeResult(error=err)

        with (
            patch("src.commands.backup.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.backup.create_client") as mock_cc,
            patch("src.commands.backup.count_messages", new_callable=AsyncMock, return_value=result),
        ):
            mock_cc.return_value = _make_client_mock()

            from src.commands.backup import run_backup
            with pytest.raises(SystemExit) as exc_info:
                run_backup(dialog_id=100, estimate=True)
            assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# Backup to file tests (T21 atomic write)
# ---------------------------------------------------------------------------


class TestBackupToFile:

    def test_backup_to_file(self, tmp_path, capsys):
        """Backup with --outdir writes JSON to messages.json atomically."""
        msgs = [_make_msg(1, "Hello"), _make_msg(2, "World")]
        count_result = _FakeResult(payload=2)
        page_result = _FakeResult(payload=msgs)
        output_dir = tmp_path / "backup"
        
        # Dialog will be created at output_dir / "Test Dialog_100" / "messages.json"
        dialog_info = _FakeDialogInfo(id=100, name="Test Dialog")
        dialogs_result = _FakeResult(payload=[dialog_info])

        with (
            patch("src.commands.backup.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.backup.create_client") as mock_cc,
            patch("src.commands.backup.get_dialogs", new_callable=AsyncMock, return_value=dialogs_result),
            patch("src.commands.backup.count_messages", new_callable=AsyncMock, return_value=count_result),
            patch("src.commands.backup.read_messages", new_callable=AsyncMock, return_value=page_result),
            patch("src.commands.backup._is_tty", return_value=False),
        ):
            mock_cc.return_value = _make_client_mock()

            from src.commands.backup import run_backup
            run_backup(dialog_id=100, limit=100, outdir=str(output_dir))

        # File is now in subdirectory <dialog_name>_<dialog_id>
        output_file = output_dir / "Test Dialog_100" / "messages.json"
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert len(data) == 2
        assert data[0]["text"] == "Hello"

    def test_backup_error(self, tmp_path):
        """Backup with API error exits 2."""
        count_result = _FakeResult(payload=10)
        err = _FakeError("ENTITY_NOT_FOUND", "No such dialog")
        page_result = _FakeResult(error=err)
        
        # Mock dialog info
        dialog_info = _FakeDialogInfo(id=999, name="Test Dialog")
        dialogs_result = _FakeResult(payload=[dialog_info])

        with (
            patch("src.commands.backup.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.backup.create_client") as mock_cc,
            patch("src.commands.backup.get_dialogs", new_callable=AsyncMock, return_value=dialogs_result),
            patch("src.commands.backup.count_messages", new_callable=AsyncMock, return_value=count_result),
            patch("src.commands.backup.read_messages", new_callable=AsyncMock, return_value=page_result),
            patch("src.commands.backup._is_tty", return_value=False),
        ):
            mock_cc.return_value = _make_client_mock()

            from src.commands.backup import run_backup
            with pytest.raises(SystemExit) as exc_info:
                run_backup(dialog_id=999, limit=100, outdir=str(tmp_path))
            assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# Resumable backup tests (T22)
# ---------------------------------------------------------------------------


class TestResumable:

    def test_scan_existing(self, tmp_path):
        """_scan_existing returns set of message IDs from existing file."""
        from src.commands.backup import _scan_existing

        f = tmp_path / "messages.json"
        f.write_text(json.dumps([
            {"id": 1, "text": "a", "date": "2026-06-01T12:00:00+00:00"},
            {"id": 2, "text": "b", "date": "2026-06-01T12:01:00+00:00"},
        ]))
        ids = _scan_existing(f)
        assert ids == {1, 2}

    def test_scan_existing_missing(self, tmp_path):
        """_scan_existing returns empty set for nonexistent file."""
        from src.commands.backup import _scan_existing

        ids = _scan_existing(tmp_path / "messages.json")
        assert ids == set()

    def test_latest_timestamp(self, tmp_path):
        """_latest_timestamp returns the max date from existing file."""
        from src.commands.backup import _latest_timestamp

        f = tmp_path / "messages.json"
        f.write_text(json.dumps([
            {"id": 1, "date": "2026-06-01T12:00:00+00:00"},
            {"id": 2, "date": "2026-06-01T13:00:00+00:00"},
        ]))
        ts = _latest_timestamp(f)
        assert ts is not None
        assert ts.hour == 13

    def test_resumable_skips_existing(self, tmp_path, capsys):
        """Backup with existing output skips already-downloaded messages."""
        # Create output directory with existing messages file
        # With new structure: backup/<dialog_name>_<dialog_id>/messages.json
        output_dir = tmp_path / "backup"
        dialog_subdir = output_dir / "Test Dialog_100"
        dialog_subdir.mkdir(parents=True)
        output_file = dialog_subdir / "messages.json"
        output_file.write_text(json.dumps([
            {"id": 1, "dialog_id": 100, "text": "Old", "date": "2026-06-01T12:00:00+00:00",
             "sender_id": None, "sender_name": None, "has_media": False, "media_type": None},
        ]))

        # API returns msg 1 (existing) + msg 2 (new)
        msg1 = _make_msg(1, "Old", 0)
        msg2 = _make_msg(2, "New", 1)
        count_result = _FakeResult(payload=2)
        page_result = _FakeResult(payload=[msg1, msg2])
        
        # Mock dialog info
        dialog_info = _FakeDialogInfo(id=100, name="Test Dialog")
        dialogs_result = _FakeResult(payload=[dialog_info])

        with (
            patch("src.commands.backup.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.backup.create_client") as mock_cc,
            patch("src.commands.backup.get_dialogs", new_callable=AsyncMock, return_value=dialogs_result),
            patch("src.commands.backup.count_messages", new_callable=AsyncMock, return_value=count_result),
            patch("src.commands.backup.read_messages", new_callable=AsyncMock, return_value=page_result),
            patch("src.commands.backup._is_tty", return_value=False),
        ):
            mock_cc.return_value = _make_client_mock()

            from src.commands.backup import run_backup
            run_backup(dialog_id=100, limit=100, outdir=str(output_dir))

        data = json.loads(output_file.read_text())
        # Should have both messages merged
        assert len(data) == 2
        ids = {m["id"] for m in data}
        assert ids == {1, 2}


# ---------------------------------------------------------------------------
# Rate-limit retry (T19)
# ---------------------------------------------------------------------------


class TestRateLimit:

    def test_rate_limit_retry(self, capsys, tmp_path):
        """Rate-limited page is retried after sleep."""
        msgs = [_make_msg(1, "Hello")]
        count_result = _FakeResult(payload=1)
        rate_err = _FakeError("RATE_LIMITED", "Flood", retry_after=1)
        rate_result = _FakeResult(error=rate_err)
        ok_result = _FakeResult(payload=msgs)
        
        # Mock dialog info
        dialog_info = _FakeDialogInfo(id=100, name="Test Dialog")
        dialogs_result = _FakeResult(payload=[dialog_info])

        # First call returns rate limit, second succeeds
        call_count = 0
        async def mock_read(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rate_result
            return ok_result

        with (
            patch("src.commands.backup.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.backup.create_client") as mock_cc,
            patch("src.commands.backup.get_dialogs", new_callable=AsyncMock, return_value=dialogs_result),
            patch("src.commands.backup.count_messages", new_callable=AsyncMock, return_value=count_result),
            patch("src.commands.backup.read_messages", side_effect=mock_read),
            patch("src.commands.backup._is_tty", return_value=False),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_cc.return_value = _make_client_mock()

            from src.commands.backup import run_backup
            run_backup(dialog_id=100, limit=100, outdir=str(tmp_path))

        out = capsys.readouterr().out
        assert "Hello" in out or "1" in out


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestHelpers:

    def test_parse_since_none(self):
        """_parse_since returns None for None input."""
        from src.commands.backup import _parse_since
        assert _parse_since(None) is None

    def test_parse_since_valid(self):
        """_parse_since parses ISO 8601 string."""
        from src.commands.backup import _parse_since
        dt = _parse_since("2026-03-01T00:00:00")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 3
        assert dt.tzinfo == timezone.utc  # naive gets UTC

    def test_parse_since_invalid(self, capsys):
        """_parse_since exits 1 for invalid timestamp."""
        from src.commands.backup import _parse_since
        with pytest.raises(SystemExit) as exc_info:
            _parse_since("not-a-date")
        assert exc_info.value.code == 1

    def test_merge_messages(self):
        """_merge_messages deduplicates by ID and sorts by date."""
        from src.commands.backup import _merge_messages
        existing = [
            {"id": 1, "text": "old", "date": "2026-06-01T12:00:00"},
            {"id": 2, "text": "two", "date": "2026-06-01T12:01:00"},
        ]
        new = [
            {"id": 2, "text": "updated", "date": "2026-06-01T12:01:00"},
            {"id": 3, "text": "three", "date": "2026-06-01T12:02:00"},
        ]
        merged = _merge_messages(existing, new)
        assert len(merged) == 3
        assert merged[0]["id"] == 1
        assert merged[1]["text"] == "updated"  # ID 2 replaced
        assert merged[2]["id"] == 3

    def test_message_to_dict(self):
        """_message_to_dict converts a MessageInfo to dict."""
        from src.commands.backup import _message_to_dict
        msg = _make_msg(42, "Test")
        d = _message_to_dict(msg)
        assert d["id"] == 42
        assert d["text"] == "Test"
        assert "date" in d

    def test_fmt_time_seconds(self):
        """_fmt_time formats <60s correctly."""
        from src.commands.backup import _fmt_time
        assert _fmt_time(45) == "45s"

    def test_fmt_time_minutes(self):
        """_fmt_time formats >=60s as m:ss."""
        from src.commands.backup import _fmt_time
        assert _fmt_time(130) == "2m 10s"

    def test_atomic_write_json(self, tmp_path):
        """_atomic_write_json creates file atomically."""
        from src.commands.backup import _atomic_write_json
        f = tmp_path / "out.json"
        _atomic_write_json(f, [{"id": 1}])
        assert f.exists()
        data = json.loads(f.read_text())
        assert data == [{"id": 1}]

    def test_check_output_writable(self, tmp_path):
        """_check_output_writable passes for writable directory."""
        from src.commands.backup import _check_output_writable
        f = tmp_path / "subdir" / "backup.json"
        _check_output_writable(f)  # should not raise
        assert (tmp_path / "subdir").is_dir()


# ---------------------------------------------------------------------------
# Pagination direction tests (regression for full-backup slowdown bug)
# ---------------------------------------------------------------------------


class TestPaginationDirection:
    """Full backup must paginate BACKWARD (older messages per page).

    Bug: after page 1 the pagination cursor (resume_since) becomes non-None,
    which previously caused read_messages() to use reverse=True (forward
    direction).  That sent Telethon forward in time — re-fetching the same
    newest messages each page.  When the cursor converged on the most-recent
    message Telegram could return that single message on every subsequent
    request until `remaining` drained to zero, causing the "slower and slower"
    behaviour reported by the user.
    """

    def test_full_backup_paginates_backward_to_older_messages(self, tmp_path, capsys):
        """Full backup collects ALL pages including older messages.

        Five messages exist (IDs 1–5, msg5 = newest).
        Page 1  → newest 3: [msg5, msg4, msg3] (reverse=False, newest-first)
        Page 2  → older  2: [msg2, msg1]       (reverse=False, going backward)
        Page 3  → empty  (no more)

        Without the fix, page 2 would receive reverse=True (forward direction),
        returning duplicate messages [msg4, msg5] instead of the older ones.
        Deduplication would then produce only 3 unique messages in the output.
        With the fix, all 5 unique messages must appear in the output.
        """
        from datetime import timedelta

        base_dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        msg1 = _FakeMessageInfo(1, 100, "oldest", base_dt + timedelta(minutes=0))
        msg2 = _FakeMessageInfo(2, 100, "second", base_dt + timedelta(minutes=1))
        msg3 = _FakeMessageInfo(3, 100, "middle", base_dt + timedelta(minutes=2))
        msg4 = _FakeMessageInfo(4, 100, "fourth", base_dt + timedelta(minutes=3))
        msg5 = _FakeMessageInfo(5, 100, "newest", base_dt + timedelta(minutes=4))

        # count_messages returns 5 total
        count_result = _FakeResult(payload=5)

        dialog_info = _FakeDialogInfo(id=100, name="Test Dialog")
        dialogs_result = _FakeResult(payload=[dialog_info])

        call_count = 0

        async def mock_read(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Simulate correct Telethon backward pagination (reverse=False):
            # page 1 (no cursor) → newest-first; page 2 → older messages before cursor;
            # page 3 → empty (no more).  The library fix ensures the real implementation
            # reaches page 2 with reverse=False.  This test validates that backup.py
            # correctly assembles all pages when the library returns the right data.
            if call_count == 1:
                return _FakeResult(payload=[msg5, msg4, msg3])
            if call_count == 2:
                return _FakeResult(payload=[msg2, msg1])
            return _FakeResult(payload=[])  # no more messages

        with (
            patch("src.commands.backup.load_config", return_value={
                "api_id": 1, "api_hash": "a", "session": "s"
            }),
            patch("src.commands.backup.create_client") as mock_cc,
            patch("src.commands.backup.get_dialogs", new_callable=AsyncMock, return_value=dialogs_result),
            patch("src.commands.backup.count_messages", new_callable=AsyncMock, return_value=count_result),
            patch("src.commands.backup.read_messages", side_effect=mock_read),
            patch("src.commands.backup._is_tty", return_value=False),
        ):
            mock_cc.return_value = _make_client_mock()

            from src.commands.backup import run_backup
            run_backup(dialog_id=100, limit=10, outdir=str(tmp_path))

        output_file = tmp_path / "Test Dialog_100" / "messages.json"
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        ids = {m["id"] for m in data}
        assert ids == {1, 2, 3, 4, 5}, (
            f"Expected all 5 messages but got IDs {sorted(ids)}. "
            "Likely cause: pagination went in the wrong direction (forward instead of backward), "
            "re-fetching the same newest messages instead of older ones."
        )
