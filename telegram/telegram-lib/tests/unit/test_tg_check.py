"""
Unit test for tg_check.py: verify that cmd_list() produces clean output
when the network is unreachable (no raw tracebacks, no Telethon log spam).

The test simulates a ConnectionError from Telethon and asserts that:
  - stderr contains no "Attempt" retry lines from Telethon's internal logger
  - stdout has no "Attempt" log lines either
  - The function exits via sys.exit with a clean error message
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Make tools/ importable
_tools_dir = Path(__file__).resolve().parents[2] / "tools"
sys.path.insert(0, str(_tools_dir))


@pytest.mark.asyncio
async def test_cmd_list_clean_out(capsys):
    """cmd_list must print ONLY 'Error [NETWORK_ERROR]: ...' with no extra noise."""
    fake_creds = {"api_id": 12345, "api_hash": "abc", "session": "fake"}

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(
        side_effect=ConnectionError("Connection to Telegram failed 5 time(s)")
    )
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("tg_check._load_creds", return_value=fake_creds),
        patch("tg_check._make_client", return_value=mock_client),
    ):
        from tg_check import cmd_list

        with pytest.raises(SystemExit) as exc_info:
            await cmd_list()

    captured = capsys.readouterr()
    # stdout must NOT contain Telethon retry log lines
    assert "Attempt" not in captured.out, (
        f"Telethon retry log leaked to stdout:\n{captured.out}"
    )
    # stderr must NOT contain Telethon retry log lines
    assert "Attempt" not in captured.err, (
        f"Telethon retry log leaked to stderr:\n{captured.err}"
    )
    # The exit message must be a clean error
    exit_msg = str(exc_info.value.code)
    assert "Error [NETWORK_ERROR]:" in exit_msg
    assert "Connection to Telegram failed" in exit_msg


@pytest.mark.asyncio
async def test_cmd_list_no_logs(capsys):
    """Telethon's 'Attempt N at connecting' log messages must be suppressed."""
    fake_creds = {"api_id": 12345, "api_hash": "abc", "session": "fake"}

    # Simulate what Telethon does: logs "Attempt N" then raises ConnectionError.
    telethon_logger = logging.getLogger("telethon.network.mtprotosender")

    async def _aenter_with_logs(self_):
        telethon_logger.warning("Attempt 1 at connecting failed: OSError: Network is unreachable")
        telethon_logger.warning("Attempt 2 at connecting failed: OSError: Network is unreachable")
        raise ConnectionError("Connection to Telegram failed 5 time(s)")

    mock_client = MagicMock()
    mock_client.__aenter__ = _aenter_with_logs
    mock_client.__aexit__ = AsyncMock(return_value=False)

    # Import tg_check first to trigger its module-level log suppression
    import tg_check  # noqa: F401 — triggers setLevel(CRITICAL)

    with (
        patch("tg_check._load_creds", return_value=fake_creds),
        patch("tg_check._make_client", return_value=mock_client),
    ):
        from tg_check import cmd_list

        with pytest.raises(SystemExit):
            await cmd_list()

    captured = capsys.readouterr()
    # Neither stdout nor stderr should contain Telethon retry noise
    assert "Attempt" not in captured.out, (
        f"Telethon retry log leaked to stdout:\n{captured.out}"
    )
    assert "Attempt" not in captured.err, (
        f"Telethon retry log leaked to stderr:\n{captured.err}"
    )
